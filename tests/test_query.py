# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest
from sqlalchemy import select, func

from pipeline.db import (engine, authors, dlcs, documents)
from pipeline.cache import region
from pipeline.query import (get_or_create, get_author, get_dlc, get_document)


@pytest.yield_fixture(autouse=True)
def clear_cache():
    region.invalidate()
    yield
    region.invalidate()


@pytest.yield_fixture
def conn(db):
    c = engine().connect()
    yield c
    c.close()


def test_get_or_create_creates_new_object(conn):
    get_or_create(conn, authors, authors.c.id, '1234', mit_id='1234',
                  name='Bar, Foo')
    assert conn.execute(select([authors.c.mit_id, authors.c.name])).\
        first() == ('1234', 'Bar, Foo')


def test_get_or_create_does_not_create_existing(conn):
    get_or_create(conn, authors, authors.c.mit_id, '1234', mit_id='1234',
                  name='Bar, Foo')
    get_or_create(conn, authors, authors.c.mit_id, '1234', mit_id='1234',
                  name='Bar, Foo')
    assert conn.scalar(select([func.count('*')]).select_from(authors)) == 1


def test_get_or_create_returns_primary_key(conn):
    get_or_create(conn, authors, authors.c.mit_id, '1234', mit_id='1234',
                  name='Bar, Foo')
    p_id = conn.scalar(select([authors.c.id]))
    assert p_id == get_or_create(conn, authors, authors.c.mit_id, '1234',
                                 mit_id='1234', name='Bar, Foo')


def test_get_author_returns_primary_key(conn):
    p_key = get_author({'mitid': '1234', 'name': 'Baz, Foo'}, conn)
    assert p_key == conn.scalar(select([authors.c.id]))


def test_get_author_caches_response(conn):
    p_key = get_author({'mitid': '1234', 'name': 'Bar, Foo'}, conn)
    conn.close()
    assert p_key == get_author({'mitid': '1234', 'name': 'Bar, Foo'}, conn)


def test_get_dlc_returns_primary_key(conn):
    p_key = get_dlc({'canonical': 'The Dept. of Foo', 'display': 'Foo'}, conn)
    assert p_key == conn.scalar(select([dlcs.c.id]))


def test_get_dlc_caches_response(conn):
    p_key = get_dlc({'canonical': 'The Dept. of Foo', 'display': 'Foo'}, conn)
    conn.close()
    assert p_key == get_dlc({'canonical': 'The Dept. of Foo',
                             'display': 'Foo'}, conn)


def test_get_document_inserts_documents_without_identities(conn):
    get_document('mock://handle.com/1', 'Some Foo', [], [], conn)
    doc = conn.execute(select([documents])).first()
    assert doc['handle'] == 'mock://handle.com/1'
    assert conn.scalar(select([authors])) is None
    assert conn.scalar(select([dlcs])) is None


def test_get_document_adds_document(conn):
    a = [{'mitid': '1234', 'name': 'Bar, Foo'},
         {'mitid': '5678', 'name': 'Baz, Foo'}]
    d = [{'canonical': 'The Foo Dept.', 'display': 'Foo'},
         {'canonical': 'The Bar Dept.', 'display': 'Bar'}]
    get_document('mock://handle.com/1', 'Some Foo', a, d, conn)
    assert conn.execute(select([authors.c.mit_id])).fetchall() == \
        [('1234',), ('5678',)]
    assert conn.execute(select([dlcs.c.display_name])).fetchall() == \
        [('Foo',), ('Bar',)]
    doc = conn.execute(select([documents])).first()
    assert doc['handle'] == 'mock://handle.com/1'


def test_get_document_caches_response(conn):
    p_key = get_document('mock://handle.com/1', 'Some Foo', [], [], conn)
    conn.close()
    assert p_key == get_document('mock://handle.com/1', 'Some Foo', [], [],
                                conn)
