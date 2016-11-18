# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sqlalchemy import (Table, Column, Integer, String, MetaData, ForeignKey,
                        DateTime, Index, create_engine)


metadata = MetaData()


authors = Table('authors', metadata,
                Column('id', Integer, primary_key=True),
                Column('name', String, nullable=False),
                Column('mit_id', String, index=True, unique=True,
                       nullable=False),
                )


dlcs = Table('dlcs', metadata,
             Column('id', Integer, primary_key=True),
             Column('display_name', String, nullable=False),
             Column('canonical_name', String, index=True, unique=True,
                    nullable=False),
             )


documents = Table('documents', metadata,
                  Column('id', Integer, primary_key=True),
                  Column('handle', String, index=True, unique=True,
                         nullable=False),
                  Column('title', String),
                  )


documents_dlcs = Table('documents_dlcs', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('document_id', Integer,
                              ForeignKey('documents.id'), nullable=False),
                       Column('dlc_id', Integer, ForeignKey('dlcs.id'),
                              nullable=False),
                       Index('idx_document_dlc', 'document_id', 'dlc_id'),
                       Index('idx_dlc_document', 'dlc_id', 'document_id')
                       )


documents_authors = Table('documents_authors', metadata,
                          Column('id', Integer, primary_key=True),
                          Column('document_id', Integer,
                                 ForeignKey('documents.id'), nullable=False),
                          Column('author_id', Integer,
                                 ForeignKey('authors.id'), nullable=False),
                          Index('idx_document_author', 'document_id',
                                'author_id'),
                          Index('idx_author_document', 'author_id',
                                'document_id')
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
                        nullable=False, index=True),
                 )


class Engine(object):
    def __init__(self):
        self._engine = None

    def __call__(self):
        return self._engine

    def configure(self, conn):
        self._engine = self._engine or create_engine(conn)


engine = Engine()
