# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest

from pipeline.request_writer import (buffered, BufferedMongoWriter,
                                     BufferedSolrWriter,)


@pytest.fixture
def f():
    def fn(self, x=None):
        return x
    return fn


def test_buffered_buffers_function(f):
    fn = buffered(2)(f)

    assert fn(None, 1) is None
    assert fn(None, 2) == [1, 2]
    assert fn(None, 3) is None
    assert fn(None, 4) == [3, 4]


def test_buffered_function_flushes_when_called_without_args(f):
    fn = buffered(10)(f)
    fn(None, 1)
    assert fn(None) == [1]


def test_mongo_writer_adds_requests(mongo):
    m = BufferedMongoWriter('foo', 'bar', ['localhost', mongo.port])
    m.write({'foo': 'bar'})
    m.write()
    assert m.collection.count({'foo': 'bar'}) == 1


def test_mongo_writer_flushes_on_exit(mongo):
    with BufferedMongoWriter('foo', 'bar', ['localhost', mongo.port]) as m:
        m.write({'foo': 'gaz'})
    assert m.collection.count({'foo': 'gaz'}) == 1


def test_solr_writer_adds_request(solr_add):
    s = BufferedSolrWriter('http://example.com')
    s.write({'foo': 'bar'})
    s.write()
    solr_add.assert_called_once_with([{'foo': 'bar'}])


def test_solr_writer_flushes_on_exit(solr_add):
    with BufferedSolrWriter('http://example.com') as s:
        s.write({'foo': 'bar'})
    solr_add.assert_called_once_with([{'foo': 'bar'}])
