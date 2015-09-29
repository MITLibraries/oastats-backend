# -*- coding: utf-8 -*-
from __future__ import absolute_import

from mock import patch
import pytest
import yaml
import arrow

from pipeline.pipeline import (run, process, load_identities,
                               generate_identities)


@pytest.yield_fixture
def ids(identities):
    with open(identities) as fp:
        yield fp


def test_run_adds_requests_to_mongo(mongo):
    with patch('pipeline.pipeline.process') as mock:
        mock.side_effect = [{'foo': 'bar'}, {'foo': 'baz'}]
        run(['foo', 'bar'], MONGO_DB='oastats', MONGO_COLLECTION='requests',
            MONGO_CONNECTION='mongodb://localhost:%d' % mongo.port)
    assert mongo.client().oastats.requests.count({'foo': 'baz'}) == 1
    assert mongo.client().oastats.requests.count({'foo': 'bar'}) == 1


def test_load_identities_returns_list_of_identities(ids):
    rows = load_identities(ids)
    assert next(rows) == {
        'Author': 'Bar, Foo', 'ID': '1234', 'Date Issued': '2015-01',
        'URI': 'http://example.com/1', 'Match count': '1 match',
        'MIT ID': '1000', 'Column': ''
    }
    assert next(rows) == {
        'Author': 'Baz, Foo', 'ID': '5678', 'Date Issued': '2015-01',
        'URI': 'http://example.com/2', 'Match count': '2 matches',
        'MIT ID': '2000', 'Column': 'abc'
    }


def test_generate_identities_yields_records():
    idents = generate_identities([
        {'URI': 1, 'Author': 'Foo', 'MIT ID': '1234'},
        {'URI': 2, 'Author': 'Baz', 'MIT ID': '3456'},
        {'URI': 1, 'Author': 'Bar', 'MIT ID': '2345'},
        {'URI': 2, 'Author': 'Gaz', 'MIT ID': ''}])

    assert next(idents) == \
        {'handle': 1, 'ids': [{'name': 'Foo', 'mitid': '1234'},
                              {'name': 'Bar', 'mitid': '2345'}]}
    assert next(idents) == \
        {'handle': 2, 'ids': [{'name': 'Baz', 'mitid': '3456'},
                              {'name': 'Gaz', 'mitid': ''}]}


def test_process_returns_fully_built_request(cfg):
    with open(cfg) as fp:
        config = yaml.load(fp)
    with patch('pipeline.dspace._make_request') as mock:
        mock.return_value = {
            'success': True,
            'title': 'The Effects of Foo on Bar',
            'ids': [[{'mitid': '1234', 'name': 'Bar, Foo'}]],
            'departments': [{'display': 'Dept. of Foo', 'canonical': 'MIT Foo'}],
            'uri': 'http://example.com/1'
        }
        r = process('1.2.3.4 - - [31/Jan/2013:23:58:51 -0500] "GET /openaccess-disseminate/1721.1/22774 HTTP/1.1" 200 6865 "-" "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.4; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2"',
                    config)
    assert r == {
        'title': 'The Effects of Foo on Bar',
        'authors': [{'mitid': '1234', 'name': 'Bar, Foo'}],
        'dlcs': [{'display': 'Dept. of Foo', 'canonical': 'MIT Foo'}],
        'handle': 'http://example.com/1',
        'time': arrow.get('2013-01-31T23:58:51-0500'),
        'request': '/openaccess-disseminate/1721.1/22774',
        'country': 'AUS',
        'filesize': '6865',
        'ip_address': '1.2.3.4',
        'referer': '-',
        'status': '200',
        'user_agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.4; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2',
    }
