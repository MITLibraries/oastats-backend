# -*- coding: utf-8 -*-
from __future__ import absolute_import
from operator import itemgetter

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
