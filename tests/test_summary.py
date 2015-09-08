# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest
from mock import Mock

from pipeline.summary import *


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


@pytest.fixture
def solr_result():
    result = Mock()
    result.grouped = {
        'handle': {
            'ngroups': 2,
            'matches': 10
        }
    }
    result.facets = {
        'facet_fields': {
            'country': ['USA', 10, 'ISL', 4]
        },
        'facet_ranges': {
            'time': {
                'counts': ['2015-01-01T00:00:00Z', 3, '2015-02-01T00:00:00Z', 5]
            }
        }
    }
    return result


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


def test_authors_returns_iterator_of_authors(mongo):
    a = [{'authors': [{'mitid': '1234', 'name': 'Captain Snuggles'},
                      {'mitid': '7890', 'name': 'Muffinpants'}]},
         {'authors': [{'mitid': '7890', 'name': 'Muffinpants'}]}]
    mongo.client().oastats.requests.insert(a)
    assert list(authors(mongo.client().oastats.requests)) == [
        {'mitid': '1234', 'name': 'Captain Snuggles'},
        {'mitid': '7890', 'name': 'Muffinpants'}]


def test_authors_filters_out_authors_without_mitid(mongo):
    a = [{'authors': [{'mitid': '1234', 'name': 'Captain Snuggles'}]},
         {'authors': [{'name': 'Muffinpants'}]}]
    mongo.client().oastats.requests.insert(a)
    assert list(authors(mongo.client().oastats.requests)) == [
        {'mitid': '1234', 'name': 'Captain Snuggles'}]


def test_authors_filters_out_authors_with_empty_mitid(mongo):
    a = [{'authors': [{'mitid': '1234', 'name': 'Captain Snuggles'}]},
         {'authors': [{'mitid': '', 'name': 'Muffinpants'}]}]
    mongo.client().oastats.requests.insert(a)
    assert list(authors(mongo.client().oastats.requests)) == [
        {'mitid': '1234', 'name': 'Captain Snuggles'}]


def test_get_author_returns_solr_query():
    assert get_author({'mitid': 1234, 'name': 'Fluffy'}) == \
        ('author_id:"1234"', {'rows': 0, 'wt': 'json', 'group': 'true',
                              'group.field': 'handle', 'group.ngroups': 'true'})


def test_create_author_creates_mongo_insert(solr_result):
    assert create_author(solr_result) == {
        '$set': {
            'type': 'author',
            'size': 2,
            'downloads': 10,
            'countries': [{'country': 'USA', 'downloads': 10},
                          {'country': 'ISL', 'downloads': 4}],
            'dates': [{'date': '2015-01-01', 'downloads': 3},
                      {'date': '2015-02-01', 'downloads': 5}]
        }
    }


def test_get_dlc_returns_solr_query():
    assert get_dlc({'canonical': 'Dept of Things', 'display': 'Things'}) == \
        ('dlc_canonical:"Dept of Things"', {'rows': 0, 'wt': 'json', 'group': 'true',
                                            'group.field': 'handle',
                                            'group.ngroups': 'true'})


def test_create_dlc_creates_mongo_insert(solr_result):
    assert create_dlc(solr_result) == {
        '$set': {
            'type': 'dlc',
            'size': 2,
            'downloads': 10,
            'countries': [{'country': 'USA', 'downloads': 10},
                          {'country': 'ISL', 'downloads': 4}],
            'dates': [{'date': '2015-01-01', 'downloads': 3},
                      {'date': '2015-02-01', 'downloads': 5}]
        }
    }


def test_dictify_converts_facet_count_to_dictionary():
    assert dictify("foo", ['FOO', 1, 'BAR', 2, 'BAZ', 3]) == [
        {'foo': 'FOO', 'downloads': 1}, {'foo': 'BAR', 'downloads': 2},
        {'foo': 'BAZ', 'downloads': 3}]
