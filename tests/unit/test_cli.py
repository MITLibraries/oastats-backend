# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import sys

import pytest
from mock import patch
import click
from click.testing import CliRunner

from pipeline.cli import main, SOLR_DATE


@pytest.fixture
def runner():
    return CliRunner()


def test_pipeline_requires_dspace_option(runner, geolite, logging_cfg):
    with patch('pipeline.cli.run') as mock:
        result = runner.invoke(main, ['pipeline', '--geo-ip', geolite,
                               '--logging-config', logging_cfg], input='Foo\n')
    assert result.exit_code == 2
    assert 'You must specify the URL' in result.output


def test_pipeline_checks_for_geoip_db(runner):
    with patch('pipeline.cli.run') as mock:
        result = runner.invoke(main, ['pipeline', '--geo-ip', 'foobar'],
                               input='Foo\n')
    assert result.exit_code == 2
    assert 'Invalid value for "--geo-ip"' in result.output


def test_index_adds_request(runner, mongo):
    mongo.client().oastats.requests.insert([{'foo': 'bar'}, {'foo': 'baz'}])
    with patch('pipeline.cli.idx') as mock:
        runner.invoke(main, ['index', 'http://example.com/solr', '--mongo',
                      'mongodb://localhost:%d' % mongo.port])
        assert mock.call_args[0][0].count() == 2  # Mongo cursor
        assert mock.call_args[0][1] == 'http://example.com/solr'


def test_summary_validates_date(runner, mongo):
    with patch('pipeline.cli.summarize'):
        r = runner.invoke(main, ['summary', 'http://example.com/solr', 'FOOBAR',
                          '--mongo', 'mongodb://localhost:%d' % mongo.port])
        assert r.exception is not None
        assert 'FOOBAR is not a valid date format' in r.output


def test_summary_summarizes_collection(runner, mongo):
    with patch('pipeline.cli.summarize') as mock:
        runner.invoke(main, ['summary', 'http://example.com/solr',
                      '2015-01-01T00:00:00Z', '--mongo',
                      'mongodb://localhost:%d' % mongo.port])
        args = mock.call_args[0]
        assert args[0].full_name == 'oastats.requests'
        assert args[1].full_name == 'oastats.summary'
        assert args[2:] == ('http://example.com/solr', '2015-01-01T00:00:00Z', 1)


def test_solr_date_type_fails_on_incorrect_format(runner):
    @click.command()
    @click.argument('foo', type=SOLR_DATE)
    def cli(foo):
        return foo

    r = runner.invoke(cli, ['FOOBAR'])
    assert r.exception is not None


def test_solr_date_type_passes_valid_date_type_through(runner):
    @click.command()
    @click.argument('foo', type=SOLR_DATE)
    def cli(foo):
        click.echo(foo)

    r = runner.invoke(cli, ['2015-01-01T00:00:00Z'])
    assert r.exception is None
    assert r.output == '2015-01-01T00:00:00Z\n'


@pytest.mark.skipif(sys.version_info.major < 3, reason="requires python3")
def test_generate_ids_outputs_list_of_json_objects(runner, identities):
    r = runner.invoke(main, ['generate_ids', identities])
    out = r.output.split('\n')
    assert json.loads(out[0]) == {
        'handle': 'http://example.com/1',
        'ids': [{'name': 'Bar, Foo', 'mitid': '1000'},
                {'name': 'Gaz, Foo', 'mitid': '3000'}]
    }
    assert json.loads(out[1]) == {
        'handle': 'http://example.com/2',
        'ids': [{'name': 'Baz, Foo', 'mitid': '2000'}]
    }


@pytest.mark.skipif(sys.version_info.major < 3, reason="requires python3")
def test_generate_ids_handles_non_ascii(runner, identities):
    r = runner.invoke(main, ['generate_ids', identities])
    out = r.output.split('\n')
    assert json.loads(out[2]) == {
        'handle': 'http://example.com/3',
        'ids': [{'name': 'βar, Foo', 'mitid': '0001'}]
    }
