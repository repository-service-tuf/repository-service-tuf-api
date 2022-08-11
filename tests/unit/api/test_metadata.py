import pretend
from fastapi import status
from securesystemslib.exceptions import StorageError


def test_metadata(monkeypatch):
    monkeypatch.setenv(
        "KAPRIEN_LOCAL_STORAGE_BACKEND_PATH", "tests/data_examples/metadata"
    )

    from fastapi.testclient import TestClient

    from app import kaprien_app

    test_client = TestClient(kaprien_app)

    url = "/api/v1/metadata/"

    response = test_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.url == test_client.base_url + url
    assert "root" in response.json().get("data")
    assert "snapshot" in response.json().get("data")
    assert "targets" in response.json().get("data")
    assert "timestamp" in response.json().get("data")
    assert "bins-f" in response.json().get("data")


def test_metadata_without_metadata(test_client, monkeypatch):

    url = "/api/v1/metadata/"
    mocked_check_metadata = pretend.stub(
        from_file=pretend.raiser(StorageError("Not found."))
    )
    monkeypatch.setattr(
        "kaprien_api.metadata.tuf.Metadata", mocked_check_metadata
    )

    response = test_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.url == test_client.base_url + url
    assert response.json() == {"detail": {"error": "Not found."}}


def test_metadata_specific_role(test_client, monkeypatch):
    monkeypatch.setenv(
        "KAPRIEN_LOCAL_STORAGE_BACKEND_PATH", "tests/data_examples/metadata"
    )

    url = "/api/v1/metadata/?rolename=root"

    response = test_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.url == test_client.base_url + url
    assert "root" in response.json().get("data")
    assert len(response.json().get("data")) == 1
    assert "snapshot" not in response.json().get("data")
    assert "targets" not in response.json().get("data")
    assert "timestamp" not in response.json().get("data")
    assert "e-f" not in response.json().get("data")


def test_metadata_invalid_role(test_client, monkeypatch):

    url = "/api/v1/metadata/?rolename=fsdfafsddaf"
    mocked_check_metadata = pretend.stub(
        from_file=pretend.raiser(
            StorageError(
                "Can't open tests/data_examples/metadata/1.fsdfafsddaf.json"
            )
        )
    )
    monkeypatch.setattr(
        "kaprien_api.metadata.tuf.Metadata", mocked_check_metadata
    )
    response = test_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.url == test_client.base_url + url
    assert response.json() == {
        "detail": {
            "error": (
                "Can't open tests/data_examples/metadata/1.fsdfafsddaf.json"
            )
        }
    }
