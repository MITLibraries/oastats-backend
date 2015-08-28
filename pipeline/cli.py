# -*- coding: utf-8 -*-
from __future__ import absolute_import
import fileinput
import logging
import logging.config

import yaml
import click

from pipeline.pipeline import run


@click.group()
def main():
    pass


@main.command()
@click.option('--config', envvar='OASTATS_SETTINGS',
              type=click.Path(exists=True, resolve_path=True))
@click.argument('logfiles', nargs=-1,
                type=click.Path(exists=True, resolve_path=True))
def pipeline(config, logfiles):
    with open(config) as fp:
        cfg = yaml.load(fp)
    logging.config.dictConfig(cfg['LOGGING'])
    log = logging.getLogger("pipeline")

    run(fileinput.input(logfiles), **cfg)

    log.info("{0} requests processed".format(fileinput.lineno()))


if __name__ == '__main__':
    main()
