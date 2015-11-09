# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import csv
from operator import itemgetter
from itertools import groupby

import apache_log_parser
import requests

from pipeline import APACHE_FIELD_MAPPINGS
from pipeline.parse_log import parse
from pipeline.request import add_country, str_to_dt, req_to_url
from pipeline.dspace import fetch_metadata
from pipeline.request_writer import BufferedMongoWriter


def run(lines, mongo, mongo_db, mongo_collection, geo_ip, dspace):
    req_log = logging.getLogger("pipeline.requests")

    with BufferedMongoWriter(mongo_db, mongo_collection, mongo) as mongo:
        for line in lines:
            try:
                request = process(line, geo_ip, dspace)
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


def process(request, geo_ip, dspace):
    """Process an Apache log request with the pipeline and return a dictionary."""
    req = parse(request, mappings=APACHE_FIELD_MAPPINGS)
    if req is not None:
        req = str_to_dt(req)
        req = add_country(req, geo_ip)
        req = req_to_url(req)
        req = fetch_metadata(req, dspace)
    return req


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
