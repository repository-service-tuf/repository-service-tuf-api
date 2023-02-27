# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from repository_service_tuf_api.rstuf_auth.models import Base


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
            "write:bootstrap "
            "read:bootstrap "
            "read:settings "
            "read:token "
            "read:tasks "
            "write:token "
            "delete:targets "
        ),
    }
    token = test_client.post(token_url, data=token_payload)
    headers = {
        "Authorization": f"Bearer {token.json()['access_token']}",
    }

    return headers


@pytest.fixture
def db_session():

    db_url = f"sqlite:///{os.path.join(os.getenv('DATA_DIR'), 'users.sqlite')}"

    engine = create_engine(db_url, connect_args={"check_same_thread": False})

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    yield session

    Base.metadata.drop_all(bind=engine)
