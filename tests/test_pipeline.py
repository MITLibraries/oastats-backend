# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest
import requests
import requests_mock

from pipeline.pipeline import (filter_by_date, filter_by_method, compose,
                               filter_by_ip, parse_into_dict, filter_bots,
                               filter_by_status, convert_datetime,
                               to_country, get_bitstream, add_identities,
                               construct_pipeline,)


@pytest.yield_fixture
def session():
    with requests.Session() as s:
        yield s


def test_compose_returns_composed_func():
    f = compose(lambda x: x.upper(), lambda x: x + 'baz', lambda x, y: x+y)
    assert f('foo', 'bar') == 'FOOBARBAZ'


def test_filter_by_date_filters(logs):
    lines = list(filter_by_date(logs, ['Aug/2015']))
    assert len(lines)
    assert all(['Aug/2015' in l for l in lines])


def test_filter_by_date_skips_filtering_if_no_date(logs):
    lines = list(filter_by_date(logs))
    assert len(lines) == 10


def test_filter_by_method_filters(logs):
    lines = list(filter_by_method(logs))
    assert len(lines)
    assert all(['GET' in l for l in lines])


def test_filter_by_ip_filters(logs):
    lines = list(filter_by_ip(logs))
    assert len(lines)
    assert all([l.startswith('18.1.1.1') for l in lines])


def test_parse_into_dict_returns_dicts(logs):
    reqs = list(parse_into_dict(logs))
    assert reqs[0]['request_url'] == '/openaccess-disseminate/1234.5/6789'
    assert reqs[0]['user_agent'] == 'ABrowser/5.0 (not really compatible)'


def test_parse_into_dict_filters_non_oa_requests(logs):
    reqs = list(parse_into_dict(logs))
    assert len(reqs) == 9


def test_filter_by_status_filters():
    requests = list(filter_by_status([{'status': '200'}, {'status': '500'}]))
    assert len(requests)
    assert all([r['status'] == '200' for r in requests])


def test_filter_bots_removes_requests():
    reqs = filter_bots([{'user_agent': 'libWWW foo bar'},
                        {'user_agent': 'foobar'},
                        {'user_agent': 'this is a Spider bot'}])
    assert len(list(reqs)) == 1


def test_convert_datetime_converts_to_iso_date():
    requests = convert_datetime([{'time': '31/Aug/2015:23:59:59 -0400'}])
    assert next(requests) == {'time': '2015-08-31T23:59:59-04:00'}


def test_to_country_converts_ip_to_country_code(geolite):
    assert to_country('18.1.1.1', geolite) == 'USA'


def test_to_country_uses_xxx_for_non_countries(geolite):
    assert to_country('127.0.0.1', geolite) == 'XXX'


def test_get_bitstream_returns_json(session):
    with requests_mock.Mocker() as m:
        m.get('mock://example.com', json={'foo': 'bar'})
        r = get_bitstream('foo/bar', 'mock://example.com', session)
        assert r['foo'] == 'bar'


def test_get_bistream_caches_requests(session):
    with requests_mock.Mocker() as m:
        m.get('mock://example.com', json={'foo': 'bar'})
        get_bitstream('123.4/5', 'mock://example.com/', session)
        get_bitstream('123.4/5', 'mock://example.com/', session)
        assert m.call_count == 1


def test_add_identities_adds_new_data(session, id_req):
    with requests_mock.Mocker() as m:
        m.get('mock://example.com', json=id_req)
        reqs = add_identities([{'request_url': '/123.4/5'}],
                              'mock://example.com/', session)
        r = next(reqs)
        assert r['title'] == id_req['title']
        assert r['dlcs'] == id_req['departments']
        assert r['authors'] == id_req['ids'][0]
        assert r['handle'] == id_req['uri']


def test_construct_pipeline_returns_generator_func(session, geolite, id_req,
                                                   logs):
    with requests_mock.Mocker() as m:
        m.get('mock://example.com', json=id_req)
        pipeline = construct_pipeline(session, geolite, 'mock://example.com',
                                      ['Aug/2015'])
        reqs = list(pipeline(logs))
        assert len(reqs) == 2
        assert reqs[0]['handle'] == 'http://example.com/1234'
