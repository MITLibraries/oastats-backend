# -*- coding: utf-8 -*-
from __future__ import absolute_import
from contextlib import closing
import fileinput

import arrow
import click
import geoip2.database
import maxminddb.const
import requests

from pipeline.db import engine
from pipeline.pipeline import construct_pipeline, to_csv
from pipeline.query import get_document


@click.group()
def main():
    pass


@main.command()
@click.argument('database')
@click.argument('files', nargs=-1, type=click.Path(exists=True,
                                                   resolve_path=True,
                                                   allow_dash=True))
@click.option('--month', '-m', multiple=True)
@click.option('--geo-ip', default='GeoLite2-Country.mmdb',
              type=click.Path(exists=True, resolve_path=True))
@click.option('--dspace', default='https://dspace.mit.edu/ws/oastats')
def pipeline(database, files, month, geo_ip, dspace):
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
