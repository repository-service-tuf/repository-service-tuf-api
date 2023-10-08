# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def test_client(monkeypatch):
    from app import rstuf_app

    client = TestClient(rstuf_app)

    return client
