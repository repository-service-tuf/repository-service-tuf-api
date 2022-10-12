API Design
==========

Context level
-------------

The ``repository-service-tuf-api``, in the context perspective, is an HTTP Rest
API for the TUF Metadata Repository that works asynchronously with the Metadata
Repository, sending the requests to a Broker.

.. uml:: ../../diagrams/repository-service-tuf-api-C1.puml


Container level
---------------

The ``repository-service-tuf-api``, in the container perspective, is a HTTP
Rest API that will receive requests from ``repository-service-tuf-cli``
(using HTTP + Token) as usual, not limited but also from third part software
using HTTP + Token.

The ``repository-service-tuf-api`` writes synchronously some data to the filesystem
``$DATA_DIR``. ``repository-service-tuf-api`` uses the file system, but the volume
is part of the OS.

``repository-service-tuf-api`` has two type of settings, **Service Configuration
Settings** and the **Repository Settings**.

**Service Configuration Settings**: To be considered service configuration
setting must be related to the ``repository-service-tuf-api`` functionality.

**Repository Settings**: Any configuration related to the
Metadata Repository. To be considered, the Repository Configuration must be
a configuration for the TUF Metadata Repository.

This configuration is stored in the ``RSTUF_REDIS_SERVER`` (Redis Server) to
efficiently distribute to the ``repository-service-tuf-worker``(s)
that execute operations in the Metadata. A copy of this settings is stored
localy in ``$DATA_DIR/repository_settings.ini``.

.. note::

    The Redis Server should have its persistent data setup and recovery
    mechanism. There is an implementation ``sync_redis`` that identifies
    that Redis doesn't have the Repository Settings and send it again.


The ``repository-service-tuf-api`` service stores the User database used to
manage the tokens in the filesystem.

All operations to the Repository Metadata, the service publish to the Broker as
a task, and ``repository-service-tuf-worker`` will consume it. The
``repository-service-tuf-worker`` publishes back to the ``RSTUF_REDIS_SERVER``,
and ``repository-service-tuf-api`` can consume it.


.. uml:: ../../diagrams/repository-service-tuf-api-C2.puml
