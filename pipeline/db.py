# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sqlalchemy import (Table, Column, Integer, String, MetaData, ForeignKey,
                        DateTime, create_engine)


metadata = MetaData()


authors = Table('authors', metadata,
                Column('id', Integer, primary_key=True),
                Column('name', String),
                Column('mit_id', String),
                )


dlcs = Table('dlcs', metadata,
             Column('id', Integer, primary_key=True),
             Column('display_name', String),
             Column('canonical_name', String),
             )


documents = Table('documents', metadata,
                  Column('id', Integer, primary_key=True),
                  Column('handle', String),
                  Column('title', String),
                  )


documents_dlcs = Table('documents_dlcs', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('document_id', Integer,
                              ForeignKey('documents.id'), nullable=False),
                       Column('dlc_id', Integer, ForeignKey('dlcs.id'),
                              nullable=False),
                       )


documents_authors = Table('documents_authors', metadata,
                          Column('id', Integer, primary_key=True),
                          Column('document_id', Integer,
                                 ForeignKey('documents.id'), nullable=False),
                          Column('author_id', Integer,
                                 ForeignKey('authors.id'), nullable=False),
                          )


requests = Table('requests', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('status', Integer),
                 Column('country', String(3)),
                 Column('url', String),
                 Column('referer', String),
                 Column('user_agent', String),
                 Column('datetime', DateTime),
                 Column('document_id', Integer, ForeignKey('documents.id'),
                        nullable=False),
                 )


class Engine(object):
    def __init__(self):
        self._engine = None

    def __call__(self):
        return self._engine

    def configure(self, conn):
        self._engine = self._engine or create_engine(conn)


engine = Engine()
