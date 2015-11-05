# -*- coding: utf-8 -*-
from __future__ import absolute_import
import fileinput
import logging
import logging.config
import re
import json
import sys

import yaml
import click
from pymongo import MongoClient

from pipeline.pipeline import run, load_identities, generate_identities
from pipeline.summary import index as idx, summarize


class SolrDateType(click.ParamType):
    name = 'solr date'
    r = re.compile('\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')

    def convert(self, value, param, ctx):
        if not self.r.match(value):
            self.fail('%s is not a valid date format' % value, param, ctx)
        return value


SOLR_DATE = SolrDateType()


@click.group()
def main():
    pass


@main.command()
@click.option('--config', envvar='OASTATS_SETTINGS',
              type=click.Path(exists=True, resolve_path=True))
@click.argument('logfiles', nargs=-1,
                type=click.Path(exists=True, resolve_path=True))
def pipeline(config, logfiles):
    cfg = _load_config(config)
    logging.config.dictConfig(cfg['LOGGING'])
    log = logging.getLogger("pipeline")

    run(fileinput.input(logfiles), **cfg)

    log.info("{0} requests processed".format(fileinput.lineno()))


@main.command()
@click.argument('solr')
@click.option('--mongo', default='mongodb://localhost:27017')
@click.option('--mongo-db', default='oastats')
@click.option('--mongo-collection', default='requests')
def index(solr, mongo, mongo_db, mongo_collection):
    client = MongoClient(mongo)
    collection = client[mongo_db][mongo_collection]
    requests = collection.find()
    idx(requests, solr)


@main.command()
@click.argument('solr')
@click.argument('end_date', type=SOLR_DATE)
@click.option('--mongo', default='mongodb://localhost:27017')
@click.option('--mongo-req-db', default='oastats')
@click.option('--mongo-req-collection', default='requests')
@click.option('--mongo-sum-db', default='oastats')
@click.option('--mongo-sum-collection', default='summary')
@click.option('--max-workers', default=1, type=click.INT)
def summary(solr, end_date, mongo, mongo_req_db, mongo_req_collection,
            mongo_sum_db, mongo_sum_collection, max_workers):
    client = MongoClient(mongo)
    requests = client[mongo_req_db][mongo_req_collection]
    summary = client[mongo_sum_db][mongo_sum_collection]
    summarize(requests, summary, solr, end_date, max_workers)


@main.command()
@click.argument('tsv', type=click.File(encoding='utf-8'))
def generate_ids(tsv):
    if sys.version_info.major < 3:
        raise click.UsageError('This subcommand requires python 3')
    ids = load_identities(tsv)
    for identity in generate_identities(ids):
        click.echo(json.dumps(identity, ensure_ascii=False))


def _load_config(cfg_file):
    with open(cfg_file) as fp:
        cfg = yaml.load(fp)
    return cfg


if __name__ == '__main__':
    main()
