# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest
from mock import Mock

from pipeline.request_writer import (buffered, BufferedMongoWriter,
                                     BufferedSolrWriter,)


@pytest.fixture
def Foo():
    class Bar(object):
        @buffered(3)
        def fn(self, request=None):
            return request
    return Bar


def test_buffered_buffers_method(Foo):
    foo = Foo()

    assert foo.fn(1) is None
    assert foo.fn(2) is None
    assert foo.fn(3) == [1, 2, 3]
    assert foo.fn(4) is None


def test_buffered_method_flushes_when_called_without_args(Foo):
    foo = Foo()
    foo.fn(1)
    assert foo.fn() == [1]


def test_buffered_does_not_write_empty_list(Foo):
    foo = Foo()
    assert foo.fn() is None


def test_mongo_writer_adds_requests(mongo):
    m = BufferedMongoWriter('foo', 'bar',
                            'mongodb://localhost:%d' % mongo.port)
    m.write({'foo': 'bar'})
    m.write()
    assert m.collection.count({'foo': 'bar'}) == 1


def test_mongo_writer_flushes_on_exit(mongo):
    with BufferedMongoWriter('foo', 'bar',
                             'mongodb://localhost:%d' % mongo.port) as m:
        m.write({'foo': 'gaz'})
    assert m.collection.count({'foo': 'gaz'}) == 1


def test_solr_writer_adds_request(solr):
    s = BufferedSolrWriter('http://example.com')
    s.write({'foo': 'bar'})
    s.write()
    solr().add.assert_called_once_with([{'foo': 'bar'}], commit=False)


def test_solr_writer_flushes_on_exit(solr):
    with BufferedSolrWriter('http://example.com') as s:
        s.write({'foo': 'bar'})
    solr().add.assert_called_once_with([{'foo': 'bar'}], commit=False)


def test_solr_writer_commits_on_exit(solr):
    with BufferedSolrWriter('http://example.com') as s:
        s.write({'foo': 'bar'})
    assert solr().commit.call_count == 1
