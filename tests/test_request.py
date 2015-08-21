# -*- coding: utf-8 -*-
from __future__ import absolute_import

import arrow

from pipeline.request import (add_country, get_alpha2_code, str_to_dt,
                              req_to_url,)


class TestRequest(object):
    def test_get_alpha2_code_matches_ip4_address(self):
        assert get_alpha2_code('18.9.22.169') == 'US'

    def test_get_alpha2_code_matches_ip6_address(self):
        assert get_alpha2_code('2002:1209:16a9:0:0:0:0:0') == 'US'

    def test_add_country_appends_three_letter_code(self):
        request = add_country({'ip_address': '18.9.22.169'})
        assert request.get('country') == 'USA'

    def test_str_to_dt_converts_timestamp_to_datetime(self):
        dt = arrow.get('1955-11-05T20:30:00-05:00').datetime
        request = str_to_dt({'time': '[05/Nov/1955:20:30:00 -0500]'})
        assert request.get('time') == dt

    def test_req_to_url_converts_to_url(self):
        request = req_to_url({'request': 'GET /foo/bar?baz HTTP/1.1'})
        assert request.get('request') == '/foo/bar?baz'
