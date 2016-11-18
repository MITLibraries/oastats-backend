# -*- coding: utf-8 -*-
from __future__ import absolute_import
from contextlib import closing
import fileinput
import logging
import logging.config

import arrow
import click
import geoip2.database
import maxminddb.const
import pymongo
import requests

from pipeline.db import engine, metadata
from pipeline.pipeline import construct_pipeline, to_csv, to_iso_date
from pipeline.query import get_document
from pipeline.summary import author_objs, dlc_objs, handle_objs, overall


logger = logging.getLogger(__name__)
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'full': {
            'format': '%(levelname)s [%(asctime)s] %(message)s in %(filename)s:%(lineno)d '
        }
    },
    'handlers': {
        'console': {
            'formatter': 'full',
            'class': 'logging.StreamHandler',
            'level': 'WARN',
            'stream': 'ext://sys.stderr'
        }
    },
    'loggers': {
        'pipeline': {
            'handlers': ['console']
        }
    }
})


@click.group()
def main():
    pass


@main.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True,
                                                   resolve_path=True,
                                                   allow_dash=True))
@click.option('--month', '-m', multiple=True)
@click.option('--geo-ip', default='GeoLite2-Country.mmdb',
              type=click.Path(exists=True, resolve_path=True))
@click.option('--dspace', default='https://dspace.mit.edu/ws/oastats')
@click.option('--database', envvar='OASTATS_DATABASE')
def pipeline(files, month, geo_ip, dspace, database):
    """
    Process the Apache logs and populate the database with identities.

    This command will process the logs and print the output to STDOUT. The
    output format is CSV suitable for passing to PostGres's COPY command.
    The field order is: status, country, url, referer, user_agent, datetime,
    document_id. Any requests which could not be processed due to malformed
    log entries will be logged to STDERR.

    IP addresses are converted to three letter country codes using the
    `GeoLite2 country database
    <http://dev.maxmind.com/geoip/geoip2/geolite2/>`_. Make sure to use the
    binary format (``.mmdb``) and that it's current; these are updated
    regularly. Pass the location of this file using the ``--geo-ip`` option.

    The pipeline can filter for log entries by date. Use the ``--month/-m``
    option to specify a month to select. This can be repeated as many times
    as desired to collect more than one month of requests. The format should
    be the same as appears in the log entries, specifically, ``MMM/YYYY``.
    If no month is provided all log entries will be processed.

    Identity data is collected from a custom Dspace identity bitstream. This
    can be specified using the ``--dspace`` option.

    The path to one or more log files should be passed as arguments to the
    pipeline. For example::

        \b
        (oastats)$ oastats pipeline -m Sep/2016 -m Oct/2016 \\
            --geo-ip data/GeoLite2.mmdb \\
            logs/2016/{09,10}/access.log 2>errors.log | output.csv
        (oastats)$ psql -d database -c "COPY requests (status, country, \\
            url, referer, user_agent, datetime, document_id) FROM STDIN \\
            WITH CSV" < output.csv

    """

    if not month:
        month = []
    dates = [arrow.get(d, ['MMM/YYYY', 'MMM-YYYY']) for d in month]
    dates = [d.format('MMM/YYYY') for d in dates]
    engine.configure(database)
    with requests.Session() as session:
        with closing(geoip2.database.Reader(geo_ip,
                     mode=maxminddb.const.MODE_MMAP)) as reader:
            with closing(engine().connect()) as conn:
                pipeline = construct_pipeline(session, reader, dspace, dates)
                for request in pipeline(fileinput.input(files)):
                    doc_id = get_document(request['handle'],
                                          request['title'],
                                          request.get('authors', []),
                                          request.get('dlcs', []),
                                          conn)
                    req = (request['status'],
                           request['country'],
                           request['request_url'],
                           request.get('referer', ''),
                           request.get('user_agent', ''),
                           request['time'],
                           str(doc_id))
                    click.echo(to_csv(req))


@main.command()
@click.option('--database', envvar='OASTATS_DATABASE')
@click.option('--mongo', default='mongodb://localhost:27017')
@click.option('--mongo-db', default='oastats')
@click.option('--mongo-coll', default='summary')
def summary(database, mongo, mongo_db, mongo_coll):
    """
    Create the summary collection in Mongo.

    The current OAStats website uses a ``summary`` collection in Mongo which
    effectively functions as a pregenerated query cache. This command will
    generate and insert the necessary JSON objects into Mongo.

    Though not required, it is recommended to create a temporary summary
    collection in Mongo and rename it to ``summary`` once this command has
    finished. For example::

        \b
        (oastats)$ oastats summary --mongo-coll summary_new
        (oastats)$ mongo oastats --eval \\
            'db.summary_new.renameCollection("summary", true)'
    """

    engine.configure(database)
    client = pymongo.MongoClient(mongo)
    collection = client[mongo_db][mongo_coll]
    with closing(engine().connect()) as conn:
        for author in author_objs(conn):
            collection.update_one({'_id': author['_id']},
                                  {'$set': author}, upsert=True)
        for dlc in dlc_objs(conn):
            collection.update_one({'_id': dlc['_id']},
                                  {'$set': dlc}, upsert=True)
        for handle in handle_objs(conn):
            collection.update_one({'_id': handle['_id']},
                                  {'$set': handle}, upsert=True)
        collection.update_one({'_id': 'Overall'},
                              {'$set': overall(conn)}, upsert=True)


@main.command()
@click.argument('command', type=click.Choice(['create', 'drop']))
@click.option('--database', envvar='OASTATS_DATABASE')
def db(command, database):
    """
    Create/drop the PostGres database tables.

    This will create or drop the database tables depending on which command
    is provided (``create`` or ``drop``). Make sure the database exists
    first.

    Example::

        (oastats)$ oastats db create

    """

    engine.configure(database)
    if command == 'create':
        metadata.create_all(engine())
    elif command == 'drop':
        if click.confirm('Are you sure you want to drop the database?'):
            metadata.drop_all(engine())


@main.command()
@click.option('--database', envvar='OASTATS_DATABASE')
@click.option('--mongo', default='mongodb://localhost:27017')
@click.option('--mongo-db', default='oastats')
@click.option('--mongo-coll', default='requests')
def load(database, mongo, mongo_db, mongo_coll):
    """
    Load the Mongo requests collection into PostGres.

    The entire Mongo requests collection will be iterated over and loaded
    into PostGres. The collection is sorted by time descending before being
    iterated. This is done in order to get the most recent (and complete)
    identitiy data from the denormalized Mongo database. It is recommended
    to make sure the requests collection has a descending index on the time
    field before running::

        \b
        (oastats)$ mongo oastats --eval \\
            "db.requests.createIndex({time: -1})"
        (oastats)$ oastats load

    """

    engine.configure(database)
    client = pymongo.MongoClient(mongo)
    collection = client[mongo_db][mongo_coll]
    with closing(engine().connect()) as conn:
        for request in collection.find().sort('time',
                                              pymongo.DESCENDING):
            doc_id = get_document(request['handle'],
                                  request['title'],
                                  request.get('authors', []),
                                  request.get('dlcs', []),
                                  conn)
            req = (request['status'],
                   request['country'],
                   request['request'],
                   request.get('referer', ''),
                   request.get('user_agent', ''),
                   request['time'].isoformat(),
                   str(doc_id))
            click.echo(to_csv(req))
