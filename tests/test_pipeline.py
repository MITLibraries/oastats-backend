# -*- coding: utf-8 -*-
from __future__ import absolute_import

from mock import patch

from pipeline.pipeline import run


def test_run_adds_requests_to_mongo(mongo):
    with patch('pipeline.pipeline.process') as mock:
        mock.side_effect = [{'foo': 'bar'}, {'foo': 'baz'}]
        run(['foo', 'bar'], MONGO_DB='oastats', MONGO_COLLECTION='requests',
            MONGO_CONNECTION=['localhost', mongo.port])
    assert mongo.client().oastats.requests.count({'foo': 'baz'}) == 1
    assert mongo.client().oastats.requests.count({'foo': 'bar'}) == 1
