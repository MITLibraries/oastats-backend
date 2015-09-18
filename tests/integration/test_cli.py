# -*- coding: utf-8 -*-
from __future__ import absolute_import

from click.testing import CliRunner
import pytest
import pysolr
import pymongo

from pipeline.cli import main


pytestmark = pytest.mark.usefixtures('clean_mongo', 'clean_solr')


@pytest.fixture
def runner():
    return CliRunner()


@pytest.mark.usefixtures('load_mongo_records')
def test_index_adds_mongo_records_to_solr(runner, solr_port, mongo_port):
    runner.invoke(main, ['index',
                         'http://localhost:%s/solr/oastats' % solr_port,
                         '--mongo', 'mongodb://localhost:%s' % mongo_port])

    solr = pysolr.Solr('http://localhost:%s/solr/oastats' % solr_port)
    r = solr.search('*:*')
    assert len(r) == 2
    doc = next(iter(r))
    assert doc['title'] == 'The Foobar'


@pytest.mark.usefixtures('load_mongo_records', 'load_solr_records')
def test_summary_summarizes_requests(runner, solr_port, mongo_port):
    runner.invoke(main, ['summary',
                         'http://localhost:%s/solr/oastats' % solr_port,
                         '2015-02-01T00:00:00Z', '--mongo',
                         'mongodb://localhost:%s' % mongo_port])
    c = pymongo.MongoClient('mongodb://localhost:%s' % mongo_port)
    a = c.oastats.summary.find_one({'_id': {'name': 'Baz, Foo',
                                            'mitid': '5678'}})
    assert a['type'] == 'author'
