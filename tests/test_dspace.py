# -*- coding: utf-8 -*-
from __future__ import absolute_import

from requests import HTTPError
import pytest
from mock import patch, Mock

import pipeline.dspace as dspace


@pytest.fixture
def dspace_response():
    response = {
        "title": "50 Shades of Hay",
        "uri": "Meadowcup",
        "departments": [
            {"canonical": "Hay There", "display": "Wut"}
        ],
        "success": True
    }
    m = Mock()
    m.json.return_value = response
    return m


@pytest.fixture
def failure_response():
    m = Mock()
    m.json.return_value = {"success": False}
    return m


@pytest.yield_fixture
def requests():
    patcher = patch('pipeline.dspace.requests')
    yield patcher.start()
    patcher.stop()


class TestDSpace(object):
    def test_get_handle_returns_handle(self):
        req_string = "http://www.example.com/foo/openaccess-disseminate/1.2/3"
        assert dspace.get_handle(req_string) == "1.2/3"

    def test_fetch_metadata_sets_properties(self, requests, dspace_response,
                                            id_svc):
        requests.get.return_value = dspace_response
        req = dspace.fetch_metadata({'request': '/openaccess-disseminate/1.2.3/4'},
                                    id_svc)
        assert req['dlcs'] == [{"canonical": "Hay There", "display": "Wut"}]
        assert req['handle'] == "Meadowcup"
        assert req['title'] == "50 Shades of Hay"

    def test_fetch_metadata_throws_exception_on_error(self, requests, id_svc):
        requests.get.return_value = Mock(**{'raise_for_status.side_effect': HTTPError})
        with pytest.raises(HTTPError):
            dspace.fetch_metadata({'request': '/openaccess-disseminate/1.2/4'},
                                  id_svc)

    def test_fetch_metadata_returns_false_on_no_success(self, requests, id_svc,
                                                        failure_response):
        requests.get.return_value = failure_response
        r = dspace.fetch_metadata({'request': '/openaccess-disseminate/1.2.3/5'},
                                  id_svc)
        assert r is False
