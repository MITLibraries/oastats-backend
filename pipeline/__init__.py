# -*- coding: utf-8 -*-
from __future__ import absolute_import

from pipeline.parse_log import parse
from pipeline.request import add_country, str_to_dt, req_to_url
from pipeline.dspace import fetch_metadata


def process(request):
    """Process an Apache log request with the pipeline and return a dictionary."""
    req = parse(request)
    if req is not None:
        req = str_to_dt(req)
        req = add_country(req)
        req = req_to_url(req)
        req = fetch_metadata(req)
    return req
