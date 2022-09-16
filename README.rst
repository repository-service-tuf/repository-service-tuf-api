################
Kaprien REST API
################

.. note::

  This project is not functional. Please wait for the first functional release
  (0.0.1)

Development
###########


Development tools
=================

- Python >=3.10
- pip
- Pipenv
- Docker


Intalling project requirements
==============================

This repository has the ``requirements.txt`` and the ``requirements-dev.txt``
files to help build your virtual environment.

We also recommend using `Pipenv <https://pipenv.pypa.io/en/latest/>`_ to manage
your virtual environment.

.. code:: shell

  $ pip install pipenv
  $ pipenv shell


Install development requirements


.. code:: shell

  $ pipenv install -d


Running kaprien-rest-api development
====================================

Github Account Token

For the development environment, you will require a Github Account Token to
download Kaprien REST API container

Access the Github page > Settings > Develop Settings > Personal Access tokens >
Generate new token

This token requires only
``read:packages Download packages from GitHub Package Registry``

Save the token hash

.. note::

    You can also build locally the
    `kaprien-repo-worker <https://github.com/kaprien/kaprien-repo-worker>`_
    image and change the `docker-compose.yml` to use the local image.


Runing the API locally

.. code:: shell

  $ make run-dev


Open http://localhost:8000/ in your browser.

Changes in the code will automatically update the service.

See Makefile for more options

kaprien-rest-api Tests
======================

We use `Tox <ttps://tox.wiki/en/latest/>`_ to manage running the tests.

Running tests

.. code:: shell

  $ tox


Managing kaprien-rest-api requirements
======================================

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
