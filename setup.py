#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from setuptools import find_packages, setup

setup(
    name="repository-service-tuf-api",
    version="0.0.1",
    url="https://github.com/repository-service-tuf/repository-service-tuf-api",
    author="Kairo de Araujo",
    author_email="kairo@dearaujo.nl",
    description="Repository Service for TUF REST API",
    packages=find_packages(),
    install_requires=["fastapi"],
)
