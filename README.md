# Kaprien REST API

---
**NOTE**

This project is not functional. Please wait for the first functional release
(0.0.1)

---

The Kaprien REST API is a RESTful API for Kaprien.

The Kaprien REST API features
- Server
  - [x] Bootstrap the Kaprien Service (initial TUF Metadata) (_sync_)
  - [x] Retrieves the latest Metadata as JSON rest API (_sync_)
  - [x] Retrieves the Kaprien Service/Metadata settings (_sync_)
- Targets
  - [ ] Add a new target file from Metadata (_async_)
  - [ ] Delete a target file from Metadata (_async_)
- Metadata
  - [ ] Bump Snapshot Metadata (_async_)
  - [ ] Bump Timestamp Metadata (_async_)
  - [ ] Bump BINS Metadata (_async_)
  - [ ] Key rotation (_async_)


The _sync_ actions are handled directly to the Metadata using the
choosed Storage Backend (`KAPRIEN_STORAGE_BACKEND`), the _async_ actions are
submitted to the Message Queue (`kaprien-mq`) and are handled by the Kaprien
Metadata Worker (`kaprien-worker`) that will manage the Metadata.

TODO: Design decisionChange to all asynchronous to avoid duplicated implementation?
- https://github.com/KAPRIEN/kaprien/issues/5



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
$ make serve-dev
```

Open http://localhost:8000/ in your browser.

Changes in the code will automatically update the service.

See Makefile for more options
### Tests

We use [Tox](https://tox.wiki/en/latest/) to manage running the tests.

Running tests
```shell
$ tox
```

### Managing the requirements

Installing new requirements

```shell
$ pipenv install {package}
```

Development requirements
```shell
$ pipenv install -d {package}
```

Updating packages
```
$ make requirements
```
