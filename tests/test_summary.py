# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest

from pipeline.summary import index


@pytest.fixture
def mongo_req():
    return {
        'handle': 'http://example.com/foo',
        'title': 'The Effects of Foo on Bar',
        'country': 'USA',
        'time': '2015-08-31T00:00:00Z',
        'dlcs': [{'display': 'Stuff n Such', 'canonical': 'Dept of Stuff'},
                 {'display': 'Other Things', 'canonical': 'Dept of Things'}],
        'authors': [{'mitid': '1234', 'name': 'Captain Snuggles'},
                    {'mitid': '7890', 'name': 'Muffinpants'}],
    }


def test_index_adds_requests_to_solr(solr):
    index([{'foo': 'bar'}, {'foo': 'baz'}], 'http://example.com')
    assert len(solr().add.call_args[0][0]) == 2


def test_index_maps_mongo_request_to_solr(solr, mongo_req):
    index([mongo_req], 'http://example.com')
    assert solr().add.call_args[0][0] == [{
        'handle': 'http://example.com/foo',
        'title': 'The Effects of Foo on Bar',
        'country': 'USA',
        'time': '2015-08-31T00:00:00Z',
        'dlc_display': ['Stuff n Such', 'Other Things'],
        'dlc_canonical': ['Dept of Stuff', 'Dept of Things'],
        'author_id': ['1234', '7890'],
        'author_name': ['Captain Snuggles', 'Muffinpants']
    }]
