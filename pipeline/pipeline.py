# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

import apache_log_parser
import requests

from pipeline import process
from pipeline.load_json import get_collection, insert


def run(lines, **kwargs):
    req_log = logging.getLogger("pipeline.requests")
    collection = get_collection(kwargs['MONGO_DB'], kwargs['MONGO_COLLECTION'],
                                kwargs['MONGO_CONNECTION'])

    req_buffer = []

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
            req_buffer.append(request)
        if len(req_buffer) > 999:
            insert(collection, req_buffer)
            req_buffer = []
    if req_buffer:
        insert(collection, req_buffer)
