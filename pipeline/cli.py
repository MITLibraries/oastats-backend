# -*- coding: utf-8 -*-
from __future__ import absolute_import
from contextlib import closing
import fileinput

import arrow
import click
import geoip2.database
import maxminddb.const
import requests

from pipeline.pipeline import construct_pipeline


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
def pipeline(files, month, geo_ip, dspace):
    if not month:
        month = []
    dates = [arrow.get(d, ['MMM/YYYY', 'MMM-YYYY']) for d in month]
    dates = [d.format('MMM/YYYY') for d in dates]
    with requests.Session() as session:
        with closing(geoip2.database.Reader(geo_ip,
                     mode=maxminddb.const.MODE_MMAP)) as reader:
            pipeline = construct_pipeline(session, reader, dspace, dates)
            for request in pipeline(fileinput.input(files)):
                req = (request['request_url'], request['country'],
                       request['time'])
                print('\t'.join(req))
