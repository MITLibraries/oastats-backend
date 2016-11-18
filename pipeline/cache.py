# -*- coding: utf-8 -*-
from __future__ import absolute_import

from dogpile.cache import make_region


def key_gen(ns, fn, **kwargs):
    fname = fn.__name__

    def generate_key(*arg):
        return fname + "_" + str(arg[0])
    return generate_key


region = make_region(
    function_key_generator=key_gen).configure('dogpile.cache.memory')
