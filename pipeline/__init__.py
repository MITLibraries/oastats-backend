# -*- coding: utf-8 -*-
from __future__ import absolute_import
from functools import wraps


APACHE_FIELD_MAPPINGS = {
    'remote_host': 'ip_address',
    'time_received': 'time',
    'request_first_line': 'request',
    'status': 'status',
    'request_header_referer': 'referer',
    'request_header_user_agent': 'user_agent',
    'response_bytes_clf': 'filesize',
}


def memoize(f):
    _cache = {}

    @wraps(f)
    def wrapper(*args):
        if args in _cache:
            val = _cache[args]
        else:
            val = _cache[args] = f(*args)
        return val
    return wrapper
