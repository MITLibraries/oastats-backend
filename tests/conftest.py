# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

import pytest


@pytest.fixture
def geolite():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, 'fixtures/GeoLite2-Country.mmdb')


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
