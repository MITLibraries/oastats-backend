# -*- coding: utf-8 -*-
from __future__ import absolute_import
import fileinput
import logging
import logging.config

import yaml
import click
import apache_log_parser
import requests

from pipeline import process
from pipeline.load_json import get_collection, insert


@click.group()
def cli():
    pass


@cli.command()
@click.option('--config', envvar='OASTATS_SETTINGS')
def pipeline(config):
    with open(config) as fp:
        cfg = yaml.load(fp)
    logging.config.dictConfig(cfg['LOGGING'])
    log = logging.getLogger("pipeline")
    req_log = logging.getLogger("pipeline.requests")

    collection = get_collection(cfg['MONGO_DB'], cfg['MONGO_COLLECTION'],
                                cfg['MONGO_CONNECTION'])

    req_buffer = []

    for line in fileinput.input():
        try:
            request = process(line, cfg)
        except apache_log_parser.ApacheLogParserException:
            req_log.error(line.strip(), extra={'err_type': 'REQUEST_ERROR'})
            continue
        except requests.exceptions.RequestException:
            req_log.error(line.strip(), extra={'err_type': 'DSPACE_ERROR'})
            continue
        except Exception, e:
            req_log.error(e, extra={'err_type': 'PROCESSING_ERROR'})
            continue
        if request:
            req_buffer.append(request)
        if len(req_buffer) > 999:
            insert(collection, req_buffer)
            req_buffer = []
    if req_buffer:
        insert(collection, req_buffer)
    log.info("{0} requests processed".format(fileinput.lineno()))


if __name__ == '__main__':
    cli()
