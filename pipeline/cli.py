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
from pipeline.pipeline import construct_pipeline, to_csv
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
    engine.configure(database)
    if command == 'create':
        metadata.create_all(engine())
    elif command == 'drop':
        if click.confirm('Are you sure you want to drop the database?'):
            metadata.drop_all(engine())
