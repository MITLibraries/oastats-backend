import futures
import pymongo
import pysolr
import logging
import sys
import argparse
import requests

parser = argparse.ArgumentParser(description="Generate Mongo summary collection from Solr")
parser.add_argument('--solr', help='Solr instance URL', required=True)
parser.add_argument('--mongo-requests',
                    help='Mongo host or MongoDB URI for requests collection')
parser.add_argument('--database-requests',
                    help='Name of Mongo database for requests collection',
                    default='oastats')
parser.add_argument('--collection-requests',
                    help='Name of Mongo collection for requests collection',
                    default='requests')
parser.add_argument('--mongo-summary',
                    help='Mongo host or MongoDB URI for summary collection')
parser.add_argument('--database-summary',
                    help='Name of Mongo database for summary collection',
                    default='oastats')
parser.add_argument('--collection-summary',
                    help='Name of Mongo collection for summary collection',
                    default='summary')
parser.add_argument('--num-threads', help='Number of threads to use', type=int,
                    default=25)
args = parser.parse_args()

num_threads = args.num_threads

solr = pysolr.Solr(args.solr)
adapter = requests.adapters.HTTPAdapter(pool_maxsize=num_threads)
solr.session.mount('http://', adapter)

mongo_requests = pymongo.MongoClient(args.mongo_requests)
requests = mongo_requests[args.database_requests][args.collection_requests]
mongo_summary = pymongo.MongoClient(args.mongo_summary)
summary = mongo_summary[args.database_summary][args.collection_summary]

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stderr))

default_params = {
    "facet": 'true',
    "facet.field": "country",
    "f.country.facet.limit": 250,
    "facet.range": "time",
    "facet.range.start": "2010-08-01T00:00:00Z",
    "facet.range.end": "NOW",
    "facet.range.gap": "+1DAY",
}

authors = dict([(int(d['mitid']), d) for d in requests.distinct("authors")])

def dictify(counts, field):
    return [{field: f[:10], "downloads": i} for f,i in zip(counts[::2], counts[1::2])]

def query_solr(query, params):
    results = solr.search(query, **params)
    return results

def update(f):
    try:
        doc = f.result()
        summary.insert(doc)
    except Exception, e:
        logger.error(e)

def get_author(author):
    query = 'author_id:"{0}"'.format(author['mitid'])
    params = {
        "rows": 0,
        "wt": "json",
        "group": "true",
        "group.field": "handle",
        "group.ngroups": "true",
    }
    res = query_solr(query, dict(default_params.items() + params.items()))
    doc = {
        "_id": author,
        "type": "author",
        "size": res.grouped['handle']['ngroups'],
        "downloads": res.grouped['handle']['matches'],
        "countries": dictify(res.facets['facet_fields']['country'], "country"),
        "dates": dictify(res.facets['facet_ranges']['time']['counts'], "date")
    }
    return doc

def get_handle(handle):
    query = 'handle:"{0}"'.format(handle)
    params = {
        "rows": 1,
        "wt": "json",
    }
    res = query_solr(query, dict(default_params.items() + params.items()))
    req = res.docs[0]
    doc = {
        "_id": handle,
        "type": "handle",
        "title": req['title'],
        "downloads": res.hits,
        "countries": dictify(res.facets['facet_fields']['country'], "country"),
        "dates": dictify(res.facets['facet_ranges']['time']['counts'], "date"),
        "parents": [authors.get(a) for a in req.get('author_id', [])]
    }
    return doc

def get_dlc(dlc):
    query = 'dlc_canonical:"{0}"'.format(dlc['canonical'])
    params = {
        "rows": 0,
        "wt": "json",
        "group": "true",
        "group.field": "handle",
        "group.ngroups": "true",
    }
    res = query_solr(query, dict(default_params.items() + params.items()))
    doc = {
        "_id": dlc,
        "type": "dlc",
        "size": res.grouped['handle']['ngroups'],
        "downloads": res.grouped['handle']['matches'],
        "countries": dictify(res.facets['facet_fields']['country'], "country"),
        "dates": dictify(res.facets['facet_ranges']['time']['counts'], "date"),
    }
    return doc

def get_summary():
    query = "*"
    params = {
        "rows": 0,
        "wt": "json",
        "group": "true",
        "group.field": "handle",
        "group.ngroups": "true",
    }
    res = query_solr(query, dict(default_params.items() + params.items()))
    doc = {
        "_id": "Overall",
        "type": "overall",
        "size": res.grouped['handle']['ngroups'],
        "downloads": res.grouped['handle']['matches'],
        "countries": dictify(res.facets['facet_fields']['country'], "country"),
        "dates": dictify(res.facets['facet_ranges']['time']['counts'], "date"),
    }
    summary.insert(doc)

def main():
    get_summary()
    with futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        for handle in requests.distinct("handle"):
            job = executor.submit(get_handle, handle)
            job.add_done_callback(update)

    with futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        for author in requests.distinct("authors"):
            job = executor.submit(get_author, author)
            job.add_done_callback(update)

    with futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        for dlc in requests.distinct("dlcs"):
            job = executor.submit(get_dlc, dlc)
            job.add_done_callback(update)


if __name__ == '__main__':
    main()
