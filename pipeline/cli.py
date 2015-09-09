# -*- coding: utf-8 -*-
from __future__ import absolute_import
import fileinput
import logging
import logging.config

import yaml
import click
from pymongo import MongoClient

from pipeline.pipeline import run
from pipeline.summary import index as idx, summarize


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
@click.option('--mongo', default='mongodb://localhost:27017')
@click.option('--mongo-req-db', default='oastats')
@click.option('--mongo-req-collection', default='requests')
@click.option('--mongo-sum-db', default='oastats')
@click.option('--mongo-sum-collection', default='summary')
@click.option('--max-workers', default=1, type=click.INT)
def summary(solr, mongo, mongo_req_db, mongo_req_collection, mongo_sum_db,
            mongo_sum_collection, max_workers):
    client = MongoClient(mongo)
    requests = client[mongo_req_db][mongo_req_collection]
    summary = client[mongo_sum_db][mongo_sum_collection]
    summarize(requests, summary, solr, max_workers)


if __name__ == '__main__':
    main()
