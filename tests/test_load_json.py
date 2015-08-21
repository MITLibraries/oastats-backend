# -*- coding: utf-8 -*-
from __future__ import absolute_import

from mongobox import MongoBox
import pytest

from pipeline.load_json import get_collection, insert


@pytest.yield_fixture
def mongo():
    box = MongoBox()
    box.start()
    yield box
    box.stop()


class TestLoadJSON(object):
    def test_get_collection_returns_mongo_collection(self, mongo):
        coll = get_collection('db1', 'col1', ('localhost', mongo.port))
        assert coll.count() == 0

    def test_insert_adds_request_to_collection(self, mongo):
        req = {'Tumblesniff': 'Bogwort'}
        coll = get_collection('db1', 'col1', ('localhost', mongo.port))
        insert(coll, req)
        assert coll.find_one() == req
