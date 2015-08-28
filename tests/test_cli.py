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
