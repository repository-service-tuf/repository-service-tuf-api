##############################
Repository Service for TUF API
##############################

.. note::

  This service is in Experimental stage.


|OpenSSF Scorecard| |Test Docker Image build| |Tests and Lint| |Coverage|

.. |OpenSSF Scorecard| image:: https://api.scorecard.dev/projects/github.com/repository-service-tuf/repository-service-tuf-api/badge
  :target: https://scorecard.dev/viewer/?uri=github.com/repository-service-tuf/repository-service-tuf-api
.. |Test Docker Image build| image:: https://github.com/repository-service-tuf/repository-service-tuf-api/actions/workflows/test_docker_build.yml/badge.svg
  :target: https://github.com/repository-service-tuf/repository-service-tuf-api/actions/workflows/test_docker_build.yml
.. |Tests and Lint| image:: https://github.com/repository-service-tuf/repository-service-tuf-api/actions/workflows/ci.yml/badge.svg
  :target: https://github.com/repository-service-tuf/repository-service-tuf-api/actions/workflows/ci.yml
.. |Coverage| image:: https://codecov.io/gh/repository-service-tuf/repository-service-tuf-api/branch/main/graph/badge.svg
 :target: https://codecov.io/gh/repository-service-tuf/repository-service-tuf-api


Repository Service for TUF API is part of `Repository Service for TUF
<https://github.com/repository-service-tuf/repository-service-tuf>`_.


Usage
=====

`Repository Service for TUF Repository API Docker Image documentation
<https://repository-service-tuf.readthedocs.io/projects/rstuf-api/en/latest/guide/Docker_README.html>`_

Development tools
=================

- Python >=3.12
- pip
- Pipenv
- Docker

Getting source code
===================

`Fork <https://docs.github.com/en/get-started/quickstart/fork-a-repo>`_ the
repository on `GitHub <https://github.com/repository-service-tuf/repository-service-tuf-api>`_
and `clone <https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository>`_
it to your local machine:

.. code-block:: console

    git clone git@github.com:YOUR-USERNAME/repository-service-tuf-api.git

Add a `remote
<https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/configuring-a-remote-for-a-fork>`_
and regularly `sync <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork>`_
to make sure you stay up-to-date with our repository:

.. code-block:: console

    git remote add upstream https://github.com/repository-service-tuf/repository-service-tuf-api
    git checkout main
    git fetch upstream
    git merge upstream/main


Installing project requirements
===============================

This repository uses Pipenv

We also recommend using `Pipenv <https://pipenv.pypa.io/en/latest/>`_ to manage
your virtual environment.

.. code:: shell

  $ pip install pipenv
  $ pipenv shell


Install development requirements

.. note::
  if you want to use python venv directly you can use generate the
  requirements.txt using `pipenv requirements --dev`

.. code:: shell

  $ pipenv install -d


Running checks with pre-commit:

The pre-commit tool is installed as part of the development requirements.

To automatically run checks before you commit your changes you should run:

.. code:: shell

    $ make precommit

This will install the git hook scripts for the first time and run the
``pre-commit`` tool.
Now ``pre-commit`` will run automatically on ``git commit``.


Running API development
=======================

Running the API locally

.. code:: shell

  $ make run-dev


Open http://localhost:80/ in your browser.

Changes in the code will automatically update the service.

See the `Makefile` for more options.

Tests
=====

We use `Tox <https://tox.wiki/en/latest/>`_ to manage running the tests.

Running tests

.. code:: shell

  $ tox


Managing requirements
=====================

Installing new requirements
............................

Project requirements

.. code:: shell

  $ pipenv install {package}


Development requirements

.. code:: shell

  $ pipenv install -d {package}

