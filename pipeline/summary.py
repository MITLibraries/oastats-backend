# -*- coding: utf-8 -*-
from __future__ import absolute_import
from operator import itemgetter
from functools import partial
try:
    import itertools.ifilter as filter
except ImportError:
    pass

import futures
import pysolr

from pipeline.request_writer import BufferedSolrWriter


def index(requests, solr_url):
    with BufferedSolrWriter(solr_url) as solr:
        for request in requests:
            doc = {
                'handle': request.get('handle'),
                'title': request.get('title'),
                'country': request.get('country'),
                'time': request.get('time'),
                'dlc_display': list(map(itemgetter('display'),
                                        request.get('dlcs', []))),
                'dlc_canonical': list(map(itemgetter('canonical'),
                                          request.get('dlcs', []))),
                'author_id': list(map(itemgetter('mitid'),
                                      request.get('authors', []))),
                'author_name': list(map(itemgetter('name'),
                                        request.get('authors', []))),
            }
            solr.write(doc)


def summarize(requests, summary, solr_url, end_date, max_workers):
    solr = pysolr.Solr(solr_url)
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        job = executor.submit(query_solr, solr, end_date, *get_overall())
        callback = partial(update, summary, {'_id': 'Overall'}, create_overall)
        job.add_done_callback(callback)
        for author in authors(requests):
            job = executor.submit(query_solr, solr, end_date, *get_author(author))
            callback = partial(update, summary, {'_id': author}, create_author)
            job.add_done_callback(callback)
        for dlc in requests.distinct("dlcs"):
            job = executor.submit(query_solr, solr, end_date, *get_dlc(dlc))
            callback = partial(update, summary, {'_id': dlc}, create_dlc)
            job.add_done_callback(callback)
        for handle in requests.distinct("handle"):
            job = executor.submit(query_solr, solr, end_date, *get_handle(handle))
            callback = partial(update, summary, {'_id': handle}, create_handle)
            job.add_done_callback(callback)


def update(summary, ident, formatter, result):
    query = formatter(result)
    summary.update_one(ident, query, True)


def authors(requests):
    return filter(lambda x: x.get('mitid'), requests.distinct('authors'))


def query_solr(solr, query, end_date, params={}):
    kwargs = {
        "facet": 'true',
        "facet.field": "country",
        "f.country.facet.limit": 250,
        "facet.range": "time",
        "facet.range.start": "2010-08-01T00:00:00Z",
        "facet.range.end": end_date,
        "facet.range.gap": "+1DAY",
    }
    kwargs.update(params)
    return solr.search(query, **kwargs)


def get_author(author):
    query = 'author_id:"{0}"'.format(author['mitid'])
    params = {
        "rows": 0,
        "group": "true",
        "group.field": "handle",
        "group.ngroups": "true",
    }
    return query, params


def create_author(result):
    return {
        "$set": {
            "type": "author",
            "size": result.grouped['handle']['ngroups'],
            "downloads": result.grouped['handle']['matches'],
            "countries": dictify('country',
                                 result.facets['facet_fields']['country']),
            "dates": dictify('date',
                             result.facets['facet_ranges']['time']['counts'])
        }
    }


def get_dlc(dlc):
    query = 'dlc_canonical:"{0}"'.format(dlc['canonical'])
    params = {
        "rows": 0,
        "group": "true",
        "group.field": "handle",
        "group.ngroups": "true",
    }
    return query, params


def create_dlc(result):
    return {
        "$set": {
            "type": "dlc",
            "size": result.grouped['handle']['ngroups'],
            "downloads": result.grouped['handle']['matches'],
            "countries": dictify('country',
                                 result.facets['facet_fields']['country']),
            "dates": dictify('date',
                             result.facets['facet_ranges']['time']['counts'])
        }
    }


def get_handle(handle):
    query = 'handle:"{0}"'.format(handle)
    params = {"rows": 1}
    return query, params


def create_handle(result):
    hdl = result.docs[0]
    return {
        '$set': {
            'type': 'handle',
            'title': hdl['title'],
            'downloads': result.grouped['handle']['matches'],
            'countries': dictify('country',
                                 result.facets['facet_fields']['country']),
            'dates': dictify('date',
                             result.facets['facet_ranges']['time']['counts']),
            'parents': list(map(split_author, hdl.get('author', [])))
        }
    }


def get_overall():
    params = {
        "rows": 0,
        "group": "true",
        "group.field": "handle",
        "group.ngroups": "true",
    }
    return '*', params


def create_overall(result):
    return {
        '$set': {
            'type': 'overall',
            'size': result.grouped['handle']['ngroups'],
            'downloads': result.grouped['handle']['matches'],
            'countries': dictify('country',
                                 result.facets['facet_fields']['country']),
            'dates': dictify('date',
                             result.facets['facet_ranges']['time']['counts']),
        }
    }


def dictify(field, counts):
    """Turn Solr facet counts into compound Mongo field.

    This is used to turn the country and date facet counts into the format
    required for the Mongo summary collection. For example::

        [{
            'country': 'USA',
            'downloads': 100
        }, {
            'country': 'FRA',
            'downloads': 51
        }]

    Dates are current treated as a string, so only the first 10 characters
    of the date are taken (YYYY-MM-DD), rather than converting to a datetime
    object.

    :param field: field being summarized--either `country` or `date`
    :param counts: list of Solr facet counts in format `[facet, count, ...]`
    """

    return [
        {field: f[:10], "downloads": i} for f, i in zip(counts[::2], counts[1::2])
    ]


def split_author(author):
    try:
        mitid, name = author.split(':', 1)
    except ValueError:
        return
    if mitid and name:
        return {'mitid': int(mitid), 'name': name}
