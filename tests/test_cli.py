# -*- coding: utf-8 -*-
from __future__ import absolute_import

from click.testing import CliRunner
import pytest
import requests_mock

from pipeline.cli import main


pytestmark = pytest.mark.usefixtures('db')


@pytest.yield_fixture(autouse=True)
def dspace(id_req):
    with requests_mock.Mocker() as m:
        m.get('mock://example.com/ws/', json=id_req)
        yield m


def test_pipeline_returns_requests(geolite_db, log_file):
    res = CliRunner().invoke(main, ['pipeline', '--geo-ip', geolite_db,
                                    '--dspace', 'mock://example.com/ws/',
                                    '--database', 'sqlite://', log_file])
    assert res.exit_code == 0
    req = res.output.split('\n')[0]
    assert req == '200,USA,/openaccess-disseminate/1234.5/6789,-,'\
                  'ABrowser/5.0 (not really compatible),'\
                  '2015-08-31T23:59:58-04:00,1'


def test_pipeline_filters_requests(geolite_db, log_file):
    res = CliRunner().invoke(main, ['pipeline', '--geo-ip', geolite_db,
                                    '--dspace', 'mock://example.com/ws/',
                                    '-m', 'Aug/2015', '--database',
                                    'sqlite://', log_file])
    assert res.exit_code == 0
    assert len(res.output.strip().split('\n')) == 2


def test_pipeline_reads_from_stdin(geolite_db, logs):
    res = CliRunner().invoke(main, ['pipeline', '--geo-ip', geolite_db,
                                    '--dspace', 'mock://example.com/ws/',
                                    '-m', 'Aug/2015', '-m', 'Sep/2015',
                                    '--database', 'sqlite://'],
                             input=logs.read())
    assert res.exit_code == 0
    assert len(res.output.strip().split('\n')) == 3
