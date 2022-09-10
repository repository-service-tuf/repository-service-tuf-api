################
Kaprien REST API
################

.. note::

  This project is not functional. Please wait for the first functional release
  (0.0.1)


kaprien-rest-api Development
============================

This repository has the ``requirements.txt`` and the ``requirements-dev.txt``
files to help build your virtual environment.

We also recommend using `Pipenv <https://pipenv.pypa.io/en/latest/>`_ to manage your
virtual environment.

.. code:: shell

  $ pip install pipenv
  $ pipenv shell


Install development requirements


.. code:: shell

  $ pipenv install -d


Running kaprien-rest-api development
------------------------------------


Runing the API locally

.. code:: shell

  $ make serve-dev


Open http://localhost:8000/ in your browser.

Changes in the code will automatically update the service.

See Makefile for more options

kaprien-rest-api Tests
----------------------

We use `Tox <ttps://tox.wiki/en/latest/>`_ to manage running the tests.

Running tests

.. code:: shell

  $ tox


Managing kaprien-rest-api requirements
--------------------------------------

Installing new requirements
............................

Project requirements

.. code:: shell

  $ pipenv install {package}


Development requirements

.. code:: shell

  $ pipenv install -d {package}


Updating requirements files from Pipenv
.......................................

.. code:: shell

  $ make requirements
