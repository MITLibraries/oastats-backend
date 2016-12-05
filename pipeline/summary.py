# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sqlalchemy import bindparam
from sqlalchemy.sql import select, func

from pipeline.db import (authors, documents_authors, requests, documents,
                         dlcs, documents_dlcs)


def author_objs(conn):
    sql = select([authors])
    for a in conn.execute(sql):
        yield author(a['mit_id'], conn)


def dlc_objs(conn):
    sql = select([dlcs])
    for d in conn.execute(sql):
        yield dlc(d['id'], conn)


def handle_objs(conn):
    sql = select([documents])
    for d in conn.execute(sql):
        yield handle(d['id'], conn)


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
                select([func.count()])
                    .select_from(documents_authors.join(authors))
                    .where(authors.c.mit_id==bindparam('mit_id'))
                    .label('size'),
                select([func.count()])
                    .select_from(requests_to_authors)
                    .where(authors.c.mit_id==bindparam('mit_id'))
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


def dlc(dlc_id, conn):
    requests_to_dlcs = requests.join(documents)\
                               .join(documents_dlcs)\
                               .join(dlcs)
    totals = select([
                dlcs.c.canonical_name,
                dlcs.c.display_name,
                select([func.count()])
                    .select_from(documents_dlcs.join(dlcs))
                    .where(dlcs.c.id==bindparam('dlc_id'))
                    .label('size'),
                select([func.count()])
                    .select_from(requests_to_dlcs)
                    .where(dlcs.c.id==bindparam('dlc_id'))
                    .label('downloads')
                ])\
            .where(dlcs.c.id==bindparam('dlc_id'))
    countries = select([requests.c.country, func.count().label('downloads')])\
                .select_from(requests_to_dlcs)\
                .where(dlcs.c.id==bindparam('dlc_id'))\
                .group_by(requests.c.country)
    dates = select([
                func.date_trunc('day', requests.c.datetime).label('date'),
                func.count().label('downloads')])\
            .select_from(requests_to_dlcs)\
            .where(dlcs.c.id==bindparam('dlc_id'))\
            .group_by(func.date_trunc('day', requests.c.datetime))
    dlc_obj = {'type': 'dlc'}
    res = conn.execute(totals, dlc_id=dlc_id).first()
    dlc_obj['_id'] = {'canonical': res['canonical_name'],
                      'display': res['display_name']}
    dlc_obj['size'] = res['size']
    dlc_obj['downloads'] = res['downloads']
    res = conn.execute(countries, dlc_id=dlc_id)
    for row in res:
        dlc_obj.setdefault('countries', [])\
            .append({'country': row['country'],
                     'downloads': row['downloads']})
    res = conn.execute(dates, dlc_id=dlc_id)
    for row in res:
        dlc_obj.setdefault('dates', [])\
            .append({'date': row['date'].strftime('%Y-%m-%d'),
                     'downloads': row['downloads']})
    return dlc_obj


def handle(doc_id, conn):
    totals = select([
                documents.c.title,
                documents.c.handle,
                select([func.count()])
                    .select_from(requests)
                    .where(requests.c.document_id==bindparam('doc_id'))
                    .label('downloads')
                ])\
            .where(documents.c.id==bindparam('doc_id'))
    parents = select([authors.c.name, authors.c.mit_id])\
              .select_from(authors.join(documents_authors).join(documents))\
              .where(documents.c.id==bindparam('doc_id'))
    countries = select([requests.c.country, func.count().label('downloads')])\
                .where(requests.c.document_id==bindparam('doc_id'))\
                .group_by(requests.c.country)
    dates = select([
                func.date_trunc('day', requests.c.datetime).label('date'),
                func.count().label('downloads')])\
            .where(requests.c.document_id==bindparam('doc_id'))\
            .group_by(func.date_trunc('day', requests.c.datetime))
    handle_obj = {'type': 'handle'}
    res = conn.execute(totals, doc_id=doc_id).first()
    handle_obj['_id'] = res['handle']
    handle_obj['title'] = res['title']
    handle_obj['downloads'] = res['downloads']
    res = conn.execute(parents, doc_id=doc_id)
    for row in res:
        handle_obj.setdefault('parents', [])\
            .append({'mitid': row['mit_id'], 'name': row['name']})
    res = conn.execute(countries, doc_id=doc_id)
    for row in res:
        handle_obj.setdefault('countries', [])\
            .append({'country': row['country'],
                     'downloads': row['downloads']})
    res = conn.execute(dates, doc_id=doc_id)
    for row in res:
        handle_obj.setdefault('dates', [])\
            .append({'date': row['date'].strftime('%Y-%m-%d'),
                     'downloads': row['downloads']})
    return handle_obj


def overall(conn):
    totals = select([
        select([func.count()]).select_from(requests).label('downloads'),
        select([func.count()]).select_from(documents).label('size')])
    countries = select([requests.c.country, func.count().label('downloads')])\
                    .group_by(requests.c.country)
    dates = select([func.date_trunc('day', requests.c.datetime).label('date'),
                    func.count().label('downloads')])\
                .group_by(func.date_trunc('day', requests.c.datetime))
    overall_obj = {'type': 'overall'}
    res = conn.execute(totals).first()
    overall_obj['downloads'] = res['downloads']
    overall_obj['size'] = res['size']
    res = conn.execute(countries)
    for row in res:
        overall_obj.setdefault('countries', [])\
            .append({'country': row['country'],
                     'downloads': row['downloads']})
    res = conn.execute(dates)
    for row in res:
        overall_obj.setdefault('dates', [])\
            .append({'date': row['date'].strftime('%Y-%m-%d'),
                     'downloads': row['downloads']})
    return overall_obj
