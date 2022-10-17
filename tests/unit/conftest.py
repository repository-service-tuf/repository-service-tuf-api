# SPDX-FileCopyrightText: 2022 VMware Inc
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import List

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def test_client(monkeypatch):
    monkeypatch.setattr("repository_service_tuf_api.sync_redis", lambda: None)

    from app import rstuf_app

    client = TestClient(rstuf_app)

    return client


@pytest.fixture()
def token_headers(test_client):
    token_url = "/api/v1/token/?expires=1"
    token_payload = {
        "username": "admin",
        "password": "secret",
        "scope": (
            "write:targets "
            "read:targets "
            "write:bootstrap "
            "read:bootstrap "
            "read:settings "
            "read:token "
            "read:tasks "
            "delete:targets "
        ),
    }
    token = test_client.post(token_url, data=token_payload)
    headers = {
        "Authorization": f"Bearer {token.json()['access_token']}",
    }

    return headers


@pytest.fixture()
def test_db():
    @dataclass
    class Scope:
        name: str

    @dataclass
    class User:
        id: int
        username: str
        password: str
        scopes: List[Scope]

    return (User, Scope)
