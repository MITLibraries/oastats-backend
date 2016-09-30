# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sqlalchemy.sql import select

from pipeline.db import (authors, dlcs, documents, documents_dlcs,
                         documents_authors)
from pipeline.cache import region


def get_or_create(conn, table, id_column, id, **kwargs):
    p_key = conn.scalar(select([table.c.id]).where(id_column == id))
    if p_key is None:
        r = conn.execute(table.insert(), **kwargs)
        p_key = r.inserted_primary_key[0]
    return p_key


@region.cache_on_arguments()
def get_author(author, conn):
    return get_or_create(conn, authors, authors.c.mit_id, author['mit_id'],
                         mit_id=author['mit_id'], name=author['name'])


@region.cache_on_arguments()
def get_dlc(dlc, conn):
    return get_or_create(conn, dlcs, dlcs.c.canonical_name, dlc['canonical'],
                         canonical_name=dlc['canonical'],
                         display_name=dlc['display'])


def get_document(handle, title, authors, dlcs, conn):
    with conn.begin():
        author_ids = [get_author(author, conn) for author in authors]
        print(author_ids)
        dlc_ids = [get_dlc(dlc, conn) for dlc in dlcs]
        p_key = conn.scalar(select([documents.c.id]).
                            where(documents.c.handle == handle))
        if p_key is None:
            r = conn.execute(documents.insert(), handle=handle,
                             title=title)
            p_key = r.inserted_primary_key[0]
            if dlc_ids:
                conn.execute(documents_dlcs.insert(),
                             [{'document_id': p_key, 'dlc_id': dlc}
                              for dlc
                              in dlc_ids])
            if author_ids:
                conn.execute(documents_authors.insert(),
                             [{'document_id': p_key, 'author_id': author}
                              for author
                              in author_ids])
        return p_key
