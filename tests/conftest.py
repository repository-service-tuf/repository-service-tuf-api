# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
from datetime import datetime, timezone

import pretend
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def test_client(monkeypatch):
    from app import rstuf_app

    client = TestClient(rstuf_app)

    return client


@pytest.fixture()
def fake_datetime(monkeypatch):
    fake_time = datetime(2019, 6, 16, 9, 5, 1, tzinfo=timezone.utc)
    return pretend.stub(now=pretend.call_recorder(lambda a: fake_time))
