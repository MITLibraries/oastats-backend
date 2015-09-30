# -*- coding: utf-8 -*-
from __future__ import absolute_import

from click.testing import CliRunner
import pytest
import pysolr
import pymongo
from mock import patch
import yaml
import arrow

from pipeline.cli import main


pytestmark = pytest.mark.usefixtures('clean_mongo', 'clean_solr')


@pytest.fixture
def runner():
    return CliRunner()


def test_pipeline_adds_request(runner, mongo_uri, cfg, apache_req):
    with open(cfg) as fp:
        config = yaml.load(fp)
    config['MONGO_CONNECTION'] = 'mongodb://%s' % mongo_uri
    with patch('pipeline.cli._load_config') as conf:
        with patch('pipeline.pipeline.fetch_metadata') as dspace:
            dspace.return_value = {'foo': 'bar'}
            conf.return_value = config
            runner.invoke(main, ['pipeline', '--config', cfg], apache_req)
    c = pymongo.MongoClient('mongodb://%s' % mongo_uri)
    req = c.oastats.requests.find_one()
    assert req['foo'] == 'bar'


def test_pipeline_processes_request(runner, mongo_uri, cfg, apache_req):
    with open(cfg) as fp:
        config = yaml.load(fp)
    config['MONGO_CONNECTION'] = 'mongodb://%s' % mongo_uri
    with patch('pipeline.cli._load_config') as conf:
        with patch('pipeline.pipeline.fetch_metadata') as dspace:
            conf.return_value = config
            runner.invoke(main, ['pipeline', '--config', cfg], apache_req)
            req = dspace.call_args[0][0]
    assert req == {'country': 'AUS', 'filesize': '6865',
                   'ip_address': '1.2.3.4', 'referer': '-',
                   'request': '/openaccess-disseminate/1721.1/22774',
                   'status': '200',
                   'time': arrow.get('[31/Jan/2013:23:58:51 -0500]',
                                     '[DD/MMM/YYYY:HH:mm:ss Z]').datetime,
                   'user_agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.4; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2'}


@pytest.mark.usefixtures('load_mongo_records')
def test_index_adds_mongo_records_to_solr(runner, solr_uri, mongo_uri):
    runner.invoke(main, ['index',
                         'http://%s/solr/oastats' % solr_uri,
                         '--mongo', 'mongodb://%s' % mongo_uri])

    solr = pysolr.Solr('http://%s/solr/oastats' % solr_uri)
    r = solr.search('*:*')
    assert len(r) == 2
    doc = next(iter(r))
    assert doc == {'title': 'The Foobar', 'handle': 'foobar', 'country': 'USA',
                   'time': '2015-01-01T00:00:00Z',
                   'dlc_display': ['Stuff', 'Things'],
                   'dlc_canonical': ['Dept of Stuff', 'Dept of Things'],
                   'author_id': ['1234', '5678'],
                   'author_name': ['Bar, Foo', 'Baz, Foo'],
                   'author': ['1234:Bar, Foo', '5678:Baz, Foo']}


@pytest.mark.usefixtures('load_mongo_records', 'load_solr_records')
def test_summary_summarizes_requests(runner, solr_uri, mongo_uri):
    runner.invoke(main, ['summary',
                         'http://%s/solr/oastats' % solr_uri,
                         '2015-02-01T00:00:00Z', '--mongo',
                         'mongodb://%s' % mongo_uri])
    c = pymongo.MongoClient('mongodb://%s' % mongo_uri)
    a = c.oastats.summary.find_one({'_id': {'name': 'Baz, Foo',
                                            'mitid': '5678'}})
    assert a['type'] == 'author'
