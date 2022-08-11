import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="class")
def test_client():
    from app import kaprien_app

    client = TestClient(kaprien_app)

    return client
