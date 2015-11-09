# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

import pytest
from mongobox import MongoBox
from mock import patch


@pytest.fixture
def identities():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, '../fixtures/identities.csv')


@pytest.fixture
def id_svc():
    return 'http://example.com'


@pytest.yield_fixture
def mongo():
    box = MongoBox()
    box.start()
    yield box
    box.stop()


@pytest.yield_fixture
def solr():
    patcher = patch('pysolr.Solr')
    yield patcher.start()
    patcher.stop()
