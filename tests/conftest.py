# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

import pytest
from mongobox import MongoBox
from mock import patch


@pytest.fixture
def geolite():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, 'fixtures/GeoLite2-Country.mmdb')


@pytest.fixture
def identities():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, 'fixtures/identities.csv')


@pytest.fixture
def id_svc():
    return 'http://example.com'


@pytest.fixture
def field_map():
    return {
        'remote_host': 'ip_address',
        'time_received': 'time',
        'request_first_line': 'request',
        'status': 'status',
        'request_header_referer': 'referer',
        'request_header_user_agent': 'user_agent',
        'response_bytes_clf': 'filesize',
    }


@pytest.fixture
def cfg():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, 'fixtures/test-config.yml')


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
