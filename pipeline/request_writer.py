# -*- coding: utf-8 -*-
from __future__ import absolute_import

from pymongo import MongoClient
import pysolr


def buffered(maxsize=1):
    def buffered_deco(f):
        buffered_list = []

        def wrapper(self, request=None):
            if request is not None:
                buffered_list.append(request)
                if len(buffered_list) < maxsize:
                    return
            res = f(self, list(buffered_list))
            del buffered_list[:]
            return res
        return wrapper
    return buffered_deco


class BufferedMongoWriter(object):
    def __init__(self, db, collection, conn):
        client = MongoClient(*conn)
        self.collection = client[db][collection]

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.write()

    @buffered(maxsize=1000)
    def write(self, request=None):
        self.collection.insert(request)


class BufferedSolrWriter(object):
    def __init__(self, solr_url):
        self.solr = pysolr.Solr(solr_url)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.write()

    @buffered(maxsize=10000)
    def write(self, request=None):
        self.solr.add(request)
