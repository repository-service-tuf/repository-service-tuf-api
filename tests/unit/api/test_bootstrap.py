import json

import pretend
from fastapi import status


class TestGetBoostrap:
    def test_get_boostrap_available(self, test_client, monkeypatch):

        url = "/api/v1/bootstrap/"
        fake_repo = pretend.stub(is_initialized=False)
        monkeypatch.setattr("kaprien_api.bootstrap.tuf_repository", fake_repo)

        response = test_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == test_client.base_url + url
        assert response.json() == {
            "bootstrap": False,
            "message": "System available for bootstrap.",
        }

    def test_get_boostrap_not_available(self, test_client, monkeypatch):

        url = "/api/v1/bootstrap/"
        fake_repo = pretend.stub(is_initialized=True)
        monkeypatch.setattr("kaprien_api.bootstrap.tuf_repository", fake_repo)

        response = test_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == test_client.base_url + url
        assert response.json() == {
            "bootstrap": True,
            "message": "System already has a Metadata.",
        }


class TestPostBootstrap:
    def test_post_bootstrap(self, test_client, monkeypatch):
        url = "/api/v1/bootstrap/"

        fake_metadata = pretend.stub(
            to_file=pretend.call_recorder(lambda *a, **kw: None)
        )
        fake_repo = pretend.stub(
            is_initialized=False,
        )
        fake_tuf = pretend.stub(
            Metadata=pretend.stub(
                from_dict=pretend.call_recorder(lambda *a: fake_metadata)
            ),
            JSONSerializer=pretend.call_recorder(lambda: None),
            Roles=pretend.stub(TIMESTAMP=pretend.stub(value="timestamp")),
        )
        fake_storage = pretend.stub()

        monkeypatch.setattr("kaprien_api.bootstrap.tuf", fake_tuf)
        monkeypatch.setattr("kaprien_api.bootstrap.tuf_repository", fake_repo)
        monkeypatch.setattr("kaprien_api.bootstrap.storage", fake_storage)

        with open("tests/data_examples/bootstrap/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.url == test_client.base_url + url
        assert response.json() is None

    def test_post_bootstrap_already_bootstrap(self, test_client, monkeypatch):
        url = "/api/v1/bootstrap/"

        fake_repo = pretend.stub(
            is_initialized=True,
        )

        monkeypatch.setattr("kaprien_api.bootstrap.tuf_repository", fake_repo)

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
