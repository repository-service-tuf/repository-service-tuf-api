# Kaprien REST API

---
**NOTE**

This project still not functional. Please wait for the first functional release
(0.0.1)

---

The Kaprien REST API is a RESTful API for Kaprien.

Currently, the API is not functional as it is still in the Specification development and project structure phase.

```

## Development

This repository has the ``requirements.txt`` and the ``requirements-dev.txt``
files to help build your virtual environment.

We also recommend using [Pipenv](https://pipenv.pypa.io/en/latest/) to manage your virtual environment.

```shell
$ Pip install pipenv
$ pipenv shell
```

Install development requirements
```shell
$ pipenv install -d
```

### Running the Kaprien REST API development


Runing the API locally

```shell
$ uvicorn app:kaprien_app --reload
```

Open http://localhost:8000/ in your browser.

## Tests

We use [Tox](https://tox.wiki/en/latest/) to manage running the tests.

Running tests
```shell
$ tox
```

## Managing the requirements

Installing new requirements

```shell
$ pipenv install {package}
```

Development requirements
```shell
$ pipenv install -d {package}
```

Updating packages
```shell
$ pipenv update
```

Updating the ``requirements.txt`` and ``requirements-dev.txt``
```shell
$ pipenv lock -r > requirements.txt
$ pipenv lock -r -d > requirements-dev.txt
```