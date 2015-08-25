# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import fileinput
import sys
import logging

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
    current_dir = os.path.dirname(os.path.realpath(__file__))
    os.environ.setdefault("OASTATS_SETTINGS",
                          os.path.join(current_dir, "../settings.py"))
    from pipeline.conf import settings

    log = logging.getLogger("pipeline")
    req_log = logging.getLogger("req_log")

    collection = get_collection(settings.MONGO_DB,
                                settings.MONGO_COLLECTION,
                                settings.MONGO_CONNECTION)

    req_buffer = []

    for line in fileinput.input():
        try:
            request = process(line, settings)
        except apache_log_parser.ApacheLogParserException:
            # log unparseable requests
            req_log.error(line.strip(), extra={'err_type': 'REQUEST_ERROR'})
            continue
        except requests.exceptions.RequestException:
            req_log.error(line.strip(), extra={'err_type': 'DSPACE_ERROR'})
            continue
        except Exception, e:
            log.error(e, extra={'inputfile': fileinput.filename(),
                                'inputline': fileinput.filelineno()})
            continue
        if request:
            req_buffer.append(request)
        if len(req_buffer) > 999:
            insert(collection, req_buffer)
            req_buffer = []
    if req_buffer:
        insert(collection, req_buffer)
    if not fileinput.lineno():
        sys.exit("No requests to process")
    log.info("{0} requests processed".format(fileinput.lineno()))


if __name__ == '__main__':
    cli()
