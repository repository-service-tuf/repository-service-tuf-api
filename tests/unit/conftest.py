import pytest
from fastapi.testclient import TestClient

from app import kaprien_app


@pytest.fixture
def test_client():

    client = TestClient(kaprien_app)

    return client


@pytest.fixture
def test_tuf_repo():
    from kaprien_api import tuf_repository

    tuf_repository.storage_backend._path = "tests/data_examples/metadata"

    return tuf_repository
