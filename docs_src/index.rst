Welcome to OAStats Backend's documentation!
===========================================

This is a command line application that will process the Apache logs for Dspace and generate download statistics for the OA collection.

The current version is an intermediate step in moving off Mongo to PostGres and some of the functionality will be removed once the migration is complete. As such, a separate step is still required to generate a summary collection in Mongo, but this is now done using the data from the PostGres databse.


Installation
------------

Use ``pip`` to install into a virtualenv::

    (oastats)$ pip install \
        https://github.com/MITLibraries/oastats-backend/zipball/master

This will make an ``oastats`` command available when your virtualenv is active.


Usage
-----

The ``oastats`` command has four subcommands: ``db``, ``load``, ``pipeline`` and ``summary``. The full documentation for each command can be accessed with::

    (oastats)$ oastats <subcommand> --help

Each subcommand will need to connect to the PostGres database. This can be done by providing a valid `SQLAlchemy Database URI <http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls>`_ to the ``--oastats-database`` option. You can also pass this as an environment variable instead of as a command line option using the ``OASTATS_DATABASE`` variable.


Creating the Database
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: pipeline.cli.db()

Full command documentation::

    (oastats)$ oastats db --help


Migrating the Mongo Data
~~~~~~~~~~~~~~~~~~~~~~~~

.. important::
    This subcommand will be removed once the data has been migrated.

.. autofunction:: pipeline.cli.load()

Full command documentation::

    (oastats)$ oastats load --help


Running the Pipeline
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: pipeline.cli.pipeline()

Full command documentation::

    (oastats)$ oastats pipeline --help


Generating the Summary Collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. important::
    This subcommand will be removed once Mongo is no longer needed for the main OAStats website.

.. autofunction:: pipeline.cli.summary()

Full command documentation::

    (oastats)$ oastats summary --help

