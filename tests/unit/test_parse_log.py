# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest

from pipeline import APACHE_FIELD_MAPPINGS
from pipeline.parse_log import (parse_line, parser, field_mapper, parse,
                                record_filter,)


@pytest.fixture
def log_entry():
    return '1.2.3.4 - - [31/Jan/2013:23:58:51 -0500] "GET /openaccess-disseminate/1721.1/22774 HTTP/1.1" 200 6865 "-" "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.4; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2"'


@pytest.fixture
def parsed_request():
    return {
        'status': '200',
        'ip_address': '1.2.3.4',
        'time': '[31/Jan/2013:23:58:51 -0500]',
        'request': 'GET /openaccess-disseminate/1721.1/22774 HTTP/1.1',
        'referer': '-',
        'user_agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.4; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2',
        'filesize': '6865',
    }


class TestLogParser(object):
    def test_parse_line_returns_dict_with_ip_address(self, log_entry):
        line = parse_line(log_entry, parser)
        assert line.get('remote_host') == '1.2.3.4'

    def test_field_mapper_translates_key_to_mapped_key(self):
        request = field_mapper({'%h': '1.2.3.4'}, {'%h': 'ip_address'})
        assert request.get('ip_address') == '1.2.3.4'

    def test_field_mapper_drops_unmapped_fields(self):
        request = field_mapper({'status': 'GIMME'}, {'remote_host': 'ip_address'})
        assert 'status' not in request

    def test_parse_returns_a_mapped_request(self, log_entry, parsed_request):
        request = parse(log_entry, mappings=APACHE_FIELD_MAPPINGS)
        assert request == parsed_request

    def test_filter_drops_non_200_requests(self, parsed_request):
        parsed_request['status'] = '201'
        assert record_filter(parsed_request) is None

    def test_filter_drops_non_get_requests(self, parsed_request):
        parsed_request['request'] = 'POST /openaccess-disseminate/1721.1/22774 HTTP/1.1'
        assert record_filter(parsed_request) is None

    def test_filter_drops_non_handle_requests(self, parsed_request):
        parsed_request['request'] = 'GET /foobar/1721.1/22774 HTTP/1.1'
        assert record_filter(parsed_request) is None

    def test_filter_returns_successful_get_requests(self, parsed_request):
        assert record_filter(parsed_request) == parsed_request

    def test_filter_drops_localhost_requests(self, parsed_request):
        parsed_request['ip_address'] = '127.0.0.1'
        assert record_filter(parsed_request) is None
        parsed_request['ip_address'] = '::1'
        assert record_filter(parsed_request) is None

    def test_filter_drops_monitoring_requests(self, parsed_request):
        parsed_request['ip_address'] = '18.7.27.25'
        assert record_filter(parsed_request) is None

    def test_filter_drops_crawlers_starting_with(self, parsed_request):
        parsed_request['user_agent'] = "Python shmython"
        assert record_filter(parsed_request) is None

    def test_filter_drops_crawlers_containing(self, parsed_request):
        parsed_request['user_agent'] = 'creepyCrawler'
        assert record_filter(parsed_request) is None
