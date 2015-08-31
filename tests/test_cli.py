# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest
from mock import patch
from click.testing import CliRunner
import yaml

from pipeline.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cfg_loaded(cfg):
    with open(cfg) as fp:
        return yaml.load(fp)


def test_pipeline_adds_request(runner, cfg):
    with patch('pipeline.cli.run') as mock:
        runner.invoke(main, ['pipeline', '--config', cfg], input='Foo\n')
        assert mock.call_count == 1


def test_pipeline_sets_config_from_option(runner, cfg, cfg_loaded):
    with patch('pipeline.cli.run') as mock:
        runner.invoke(main, ['pipeline', '--config', cfg], input='Foo\n')
        assert mock.call_args[1] == cfg_loaded


def test_pipeline_sets_config_from_envvar(runner, cfg, cfg_loaded):
    with patch('pipeline.cli.run') as mock:
        runner.invoke(main, ['pipeline'], input='Foo\n',
                      env={'OASTATS_SETTINGS': cfg})
        assert mock.call_args[1] == cfg_loaded


def test_index_adds_request(runner, mongo):
    mongo.client().oastats.requests.insert([{'foo': 'bar'}, {'foo': 'baz'}])
    with patch('pipeline.cli.idx') as mock:
        runner.invoke(main, ['index', 'http://example.com/solr', '--mongo',
                      'mongodb://localhost:%d' % mongo.port])
        assert mock.call_args[0][0].count() == 2  # Mongo cursor
        assert mock.call_args[0][1] == 'http://example.com/solr'
