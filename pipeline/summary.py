# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sqlalchemy import bindparam
from sqlalchemy.sql import select, func

from pipeline.db import authors, documents_authors, requests, documents


def author(mit_id, conn):
    """
    Returns an author object for insertion into mongo summary collection.

    The format is as follows:
        {"_id": {"name": <name>, "mitid": <mitid>},
         "type": "author",
         "size": <num docs>,
         "downloads": <num downloads>,
         "countries": [
            {"country": <3 ltr code>, "downloads": <num downloads>},...
         ]
         "dates": [
            {"date": <YYYY-MM-DD>, "downloads": <num>},...
         ]}
    """

    requests_to_authors = requests.join(documents)\
                                  .join(documents_authors)\
                                  .join(authors)

    totals = select([
                authors.c.mit_id,
                authors.c.name,
                select([func.count()])\
                    .select_from(documents_authors.join(authors))\
                    .where(authors.c.mit_id==bindparam('mit_id'))\
                    .label('size'),
                select([func.count()])\
                    .select_from(requests_to_authors)\
                    .where(authors.c.mit_id==bindparam('mit_id'))\
                    .label('downloads')
                ])\
             .where(authors.c.mit_id==bindparam('mit_id'))
    countries = select([requests.c.country, func.count().label('downloads')])\
                .select_from(requests_to_authors)\
                .where(authors.c.mit_id==bindparam('mit_id'))\
                .group_by(requests.c.country)
    dates = select([
                func.date_trunc('day', requests.c.datetime).label('date'),
                func.count().label('downloads')])\
            .select_from(requests_to_authors)\
            .where(authors.c.mit_id==bindparam('mit_id'))\
            .group_by(func.date_trunc('day', requests.c.datetime))

    author_obj = {'type': 'author'}
    res = conn.execute(totals, mit_id=mit_id).first()
    author_obj['_id'] = {'name': res['name'], 'mitid': res['mit_id']}
    author_obj['size'] = res['size']
    author_obj['downloads'] = res['downloads']
    res = conn.execute(countries, mit_id=mit_id)
    for row in res:
        author_obj.setdefault('countries', [])\
            .append({'country': row['country'], 'downloads': row['downloads']})
    res = conn.execute(dates, mit_id=mit_id)
    for row in res:
        author_obj.setdefault('dates', [])\
            .append({'date': row['date'].strftime('%Y-%m-%d'),
                     'downloads': row['downloads']})
    return author_obj
