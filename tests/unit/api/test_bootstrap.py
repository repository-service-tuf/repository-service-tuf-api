import json

import pretend
from fastapi import status


class TestGetBoostrap:
    def test_get_boostrap_available(self, test_client, monkeypatch):

        url = "/api/v1/bootstrap/"
        mocked_check_metadata = pretend.call_recorder(lambda: False)
        monkeypatch.setattr(
            "kaprien_api.bootstrap.check_metadata", mocked_check_metadata
        )

        response = test_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == test_client.base_url + url
        assert response.json() == {
            "bootstrap": False,
            "message": "System available for bootstrap.",
        }
        assert mocked_check_metadata.calls == [pretend.call()]

    def test_get_boostrap_not_available(self, test_client, monkeypatch):

        url = "/api/v1/bootstrap/"

        mocked_check_metadata = pretend.call_recorder(lambda: True)
        monkeypatch.setattr(
            "kaprien_api.bootstrap.check_metadata", mocked_check_metadata
        )

        response = test_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == test_client.base_url + url
        assert response.json() == {
            "bootstrap": True,
            "message": "System already has a Metadata.",
        }
        assert mocked_check_metadata.calls == [pretend.call()]


class TestPostBootstrap:
    def test_post_bootstrap(self, test_client, monkeypatch):
        url = "/api/v1/bootstrap/"

        mocked_save_settings = pretend.call_recorder(lambda *a: None)
        monkeypatch.setattr(
            "kaprien_api.bootstrap.save_settings", mocked_save_settings
        )

        mocked_check_metadata = pretend.call_recorder(lambda: False)
        monkeypatch.setattr(
            "kaprien_api.bootstrap.check_metadata", mocked_check_metadata
        )

        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None)
        )
        monkeypatch.setattr(
            "kaprien_api.bootstrap.repository_metadata",
            mocked_repository_metadata,
        )
        monkeypatch.setattr("kaprien_api.bootstrap.get_task_id", lambda: "123")

        with open("tests/data_examples/bootstrap/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload)

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.url == test_client.base_url + url
        assert response.json() == {
            "message": "Bootstrap accepted.",
            "task_id": "123",
        }

    def test_post_bootstrap_already_bootstrap(self, test_client, monkeypatch):
        url = "/api/v1/bootstrap/"

        mocked_check_metadata = pretend.call_recorder(lambda: True)
        monkeypatch.setattr(
            "kaprien_api.bootstrap.check_metadata", mocked_check_metadata
        )

        with open("tests/data_examples/bootstrap/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.url == test_client.base_url + url
        assert response.json() == {
            "detail": {"error": "System already has a Metadata."}
        }

    def test_post_bootstrap_empty_payload(self, test_client, monkeypatch):
        url = "/api/v1/bootstrap/"

        response = test_client.post(url, json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.url == test_client.base_url + url
        assert response.json() == {
            "detail": [
                {
                    "loc": ["body", "settings"],
                    "msg": "field required",
                    "type": "value_error.missing",
                },
                {
                    "loc": ["body", "metadata"],
                    "msg": "field required",
                    "type": "value_error.missing",
                },
            ]
        }
