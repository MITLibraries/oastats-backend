# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

import pytest
import pymongo
import pysolr
import yaml


@pytest.fixture
def solr_uri():
    return os.environ['SOLR_URI']


@pytest.fixture
def mongo_uri():
    return os.environ['MONGO_URI']


@pytest.fixture
def mongo_client(mongo_uri):
    return pymongo.MongoClient('mongodb://%s' % mongo_uri)


@pytest.fixture
def load_mongo_records(mongo_client):
    with open('tests/fixtures/mongo_records.yml') as fp:
        records = yaml.load(fp)
    mongo_client.oastats.requests.insert_many(records)


@pytest.fixture
def solr_client(solr_uri):
    return pysolr.Solr('http://%s/solr/oastats' % solr_uri)


@pytest.fixture
def load_solr_records(solr_client):
    with open('tests/fixtures/solr_records.yml') as fp:
        records = yaml.load(fp)
    solr_client.add(records)


@pytest.yield_fixture
def clean_mongo(mongo_client):
    yield
    mongo_client.oastats.requests.drop()
    mongo_client.oastats.summary.drop()


@pytest.yield_fixture
def clean_solr(solr_client):
    yield
    solr_client.delete(q='*:*')
