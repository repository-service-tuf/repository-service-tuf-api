# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
import os
from dataclasses import dataclass
from typing import List

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def test_client(monkeypatch):
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
            "write:bootstrap "
            "write:metadata_sign "
            "read:metadata_sign "
            "read:bootstrap "
            "write:settings "
            "read:settings "
            "read:token "
            "read:tasks "
            "write:token "
            "delete:targets "
            "delete:metadata_sign "
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


@pytest.fixture()
def get_admin_pwd():
    return os.getenv("SECRETS_RSTUF_ADMIN_PASSWORD")


@pytest.fixture()
def access_token(test_client):
    data = {
        "username": "admin",
        "password": "secret",
        "scope": "write:token read:tasks write:targets delete:targets",
        "expires": 1,
    }
    response = test_client.post("/api/v1/token", data=data)

    return response.json()["access_token"]
