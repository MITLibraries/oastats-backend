# -*- coding: utf-8 -*-
from __future__ import absolute_import

import re
import requests

from pipeline.conf import settings
from pipeline.decorators import memoize


handle_pattern = re.compile(r"/openaccess-disseminate/(?P<handle>[0-9.]+/[0-9]+)")


def fetch_metadata(request):
    data = _make_request(get_handle(request.get("request")))
    if not data.get('success'):
        return False
    request['dlcs'] = list(filter(None, data.get("departments", [])))
    request['handle'] = data.get("uri")
    request['title'] = data.get("title")
    authors = data.get("ids")
    if authors:
        request['authors'] = authors[0]
    return request


def get_handle(req_string):
    matches = handle_pattern.search(req_string)
    return matches.groupdict().get('handle')


@memoize
def _make_request(handle):
    r = requests.get(settings.DSPACE_IDENTITY_SERVICE,
                     params={'handle': handle})
    r.raise_for_status()
    return r.json()
