# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import csv
from operator import itemgetter
from itertools import groupby

import apache_log_parser
import requests

from pipeline import process
from pipeline.request_writer import BufferedMongoWriter


def run(lines, **kwargs):
    req_log = logging.getLogger("pipeline.requests")

    with BufferedMongoWriter(kwargs['MONGO_DB'], kwargs['MONGO_COLLECTION'],
                             kwargs['MONGO_CONNECTION']) as mongo:
        for line in lines:
            try:
                request = process(line, kwargs)
            except apache_log_parser.ApacheLogParserException:
                req_log.error(line.strip(), extra={'err_type': 'REQUEST_ERROR'})
                continue
            except requests.exceptions.RequestException:
                req_log.error(line.strip(), extra={'err_type': 'DSPACE_ERROR'})
                continue
            except Exception as e:
                req_log.error(e, extra={'err_type': 'PROCESSING_ERROR'})
                continue
            if request:
                mongo.write(request)


def load_identities(fp):
    dialect = csv.Sniffer().sniff(fp.read(1024))
    fp.seek(0)
    return csv.DictReader(fp, dialect=dialect)


def generate_identities(rows):
    s_rows = sorted(rows, key=itemgetter('URI'))
    for handle, identities in groupby(s_rows, itemgetter('URI')):
        record = {'handle': handle, 'ids': []}
        for identity in identities:
            record['ids'].append({
                'name': identity['Author'],
                'mitid': identity.get('MIT ID', "")
            })
        yield record
