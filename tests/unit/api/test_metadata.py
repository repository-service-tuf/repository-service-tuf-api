import pretend
from fastapi import status


def test_metadata(test_client, test_tuf_repo, monkeypatch):

    url = "/api/v1/metadata/"
    monkeypatch.setattr("kaprien_api.metadata.tuf_repository", test_tuf_repo)

    response = test_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.url == test_client.base_url + url
    assert "root" in response.json().get("data")
    assert "snapshot" in response.json().get("data")
    assert "targets" in response.json().get("data")
    assert "timestamp" in response.json().get("data")
    assert "e-f" in response.json().get("data")


def test_metadata_without_metadata(test_client, monkeypatch):

    url = "/api/v1/metadata/"
    fake_repo = pretend.stub(is_initialized=False)
    monkeypatch.setattr("kaprien_api.metadata.tuf_repository", fake_repo)

    response = test_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.url == test_client.base_url + url
    assert response.json() == {
        "detail": {"error": "No metadata found in the Storage."}
    }


def test_metadata_specific_role(test_client, test_tuf_repo, monkeypatch):

    url = "/api/v1/metadata/?rolename=root"
    monkeypatch.setattr("kaprien_api.metadata.tuf_repository", test_tuf_repo)

    response = test_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.url == test_client.base_url + url
    assert "root" in response.json().get("data")
    assert len(response.json().get("data")) == 1
    assert "snapshot" not in response.json().get("data")
    assert "targets" not in response.json().get("data")
    assert "timestamp" not in response.json().get("data")
    assert "e-f" not in response.json().get("data")


def test_metadata_invalid_role(test_client, test_tuf_repo, monkeypatch):

    url = "/api/v1/metadata/?rolename=fsdfafsddaf"
    monkeypatch.setattr("kaprien_api.metadata.tuf_repository", test_tuf_repo)

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
