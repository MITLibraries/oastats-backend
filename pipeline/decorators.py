# -*- coding: utf-8 -*-
from __future__ import absolute_import
from functools import wraps


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
