# -*- coding: utf-8 -*-
from __future__ import absolute_import
import io
import os

import geoip2.database
import maxminddb.const
import pytest

from pipeline.db import engine, metadata


@pytest.yield_fixture
def db():
    engine.configure('sqlite://')
    metadata.bind = engine()
    metadata.create_all()
    yield
    metadata.drop_all()


@pytest.fixture
def geolite_db():
    return os.path.join(_current_dir(), 'fixtures/GeoLite2-Country.mmdb')


@pytest.yield_fixture
def geolite(geolite_db):
    reader = geoip2.database.Reader(geolite_db,
                                    mode=maxminddb.const.MODE_MMAP)
    yield reader
    reader.close()


@pytest.fixture
def log_file():
    return os.path.join(_current_dir(), 'fixtures/requests.log')


@pytest.yield_fixture
def logs(log_file):
    with io.open(log_file) as fp:
        yield fp


@pytest.fixture
def id_req():
    return {
        'success': True,
        'title': 'A paper.',
        'uri': 'http://example.com/1234',
        'departments': [{
            'display': 'Foo Dept.',
            'canonical': 'The Foo Dept.'
        }],
        'ids': [[{
            'mitid': '1234',
            'name': 'Bar, Foo H.'
        }, {
            'mitid': '5678',
            'name': 'Baz, Foo H.'
        }]]
    }


def _current_dir():
    return os.path.dirname(os.path.realpath(__file__))
