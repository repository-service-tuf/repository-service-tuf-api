import os
from tempfile import TemporaryDirectory

import pytest
from fastapi import status


def test_wrong_storage_backend(monkeypatch):
    tmp = TemporaryDirectory().name
    monkeypatch.setenv("SETTINGS_FILE", os.path.join(tmp, "settings.ini"))
    monkeypatch.setenv("KAPRIEN_STORAGE_BACKEND", "InvalidStorage")

    with pytest.raises(ValueError) as err:
        from app import kaprien_app  # noqa

    assert "Invalid Storage Backend InvalidStorage" in str(err.value)


def test_localstorage_backend_missing_required_argument(monkeypatch):
    tmp = TemporaryDirectory().name
    monkeypatch.setenv("SETTINGS_FILE", os.path.join(tmp, "settings.ini"))
    monkeypatch.setenv("KAPRIEN_STORAGE_BACKEND", "LocalStorage")

    with pytest.raises(AttributeError) as err:
        from app import kaprien_app  # noqa

    assert "not attribute(s) LOCAL_STORAGE_BACKEND_PATH" in str(err.value)


def test_wrong_keyvault_backend(monkeypatch):
    tmp = TemporaryDirectory().name
    monkeypatch.setenv("SETTINGS_FILE", os.path.join(tmp, "settings.ini"))
    monkeypatch.setenv("KAPRIEN_STORAGE_BACKEND", "LocalStorage")
    monkeypatch.setenv("KAPRIEN_LOCAL_STORAGE_BACKEND_PATH", "metadata")
    monkeypatch.setenv("KAPRIEN_KEYVAULT_BACKEND", "InvalidKeyVault")

    with pytest.raises(ValueError) as err:
        from app import kaprien_app  # noqa

    assert "Invalid Key Vault Backend InvalidKeyVault" in str(err.value)


def test_localkeyvault_backend_missing_required_argument(monkeypatch):
    tmp = TemporaryDirectory().name
    monkeypatch.setenv("SETTINGS_FILE", os.path.join(tmp, "settings.ini"))
    monkeypatch.setenv("KAPRIEN_STORAGE_BACKEND", "LocalStorage")
    monkeypatch.setenv("KAPRIEN_LOCAL_STORAGE_BACKEND_PATH", "storage/")
    monkeypatch.setenv("KAPRIEN_KEYVAULT_BACKEND", "LocalKeyVault")

    with pytest.raises(AttributeError) as err:
        from app import kaprien_app  # noqa

    assert "not attribute(s) LOCAL_KEYVAULT_PATH" in str(err.value)


def test_root(test_client):
    response = test_client.get("/")

    assert response.url == test_client.base_url + "/"
    assert response.status_code == status.HTTP_200_OK
    assert "Kaprien Rest API" in response.text


def test_default_notfound(test_client):
    response = test_client.get("/invalid_url")

    assert response.url == test_client.base_url + "/invalid_url"
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Not Found"}
