import pysolr
import pymongo
from operator import itemgetter
import argparse


def index(**kwargs):
    solr = pysolr.Solr(kwargs.get('solr'))
    mongo = pymongo.MongoClient(kwargs.get('mongohost'))
    requests = mongo[kwargs.get('database')][kwargs.get('collection')]

    solr_buffer = []

    for request in requests.find():
        solrdoc = {
            'handle': request.get('handle'),
            'title': request.get('title'),
            'country': request.get('country'),
            'time': request.get('time'),
            'dlc_display': map(itemgetter('display'), request.get('dlcs', [])),
            'dlc_canonical': map(itemgetter('canonical'), request.get('dlcs', [])),
            'author_id': map(itemgetter('mitid'), request.get('authors', [])),
            'author_name': map(itemgetter('name'), request.get('authors', [])),
        }
        solr_buffer.append(solrdoc)

        if len(solr_buffer) > 9999:
            solr.add(solr_buffer, commit=False)
            solr_buffer = []

    if solr_buffer:
        solr.add(solr_buffer)

    solr.commit()

def main():
    parser = argparse.ArgumentParser(description="Index Mongo collection in Solr")
    parser.add_argument('-s' , '--solr', help='Solr instance URL', required=True)
    parser.add_argument('-m', '--mongohost', help='Mongo host or MongoDB URI')
    parser.add_argument('-d', '--database', default='oastats')
    parser.add_argument('-c', '--collection', default='requests')
    args = parser.parse_args()
    index(**vars(args))


if __name__ == '__main__':
    main()
