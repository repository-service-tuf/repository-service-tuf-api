# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json

import pretend
from fastapi import status


class TestPostMetadata:
    def test_post_metadata(self, test_client, monkeypatch, token_headers):
        url = "/api/v1/metadata/"

        mocked_check_metadata = pretend.call_recorder(lambda: True)
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.is_bootstrap_done",
            mocked_check_metadata,
        )

        mocked_async_result = pretend.stub(state="SUCCESS")
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None),
            AsyncResult=pretend.call_recorder(lambda *a: mocked_async_result),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.repository_metadata",
            mocked_repository_metadata,
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.get_task_id", lambda: "123"
        )

        with open(
            "tests/data_examples/metadata/update-root-payload.json"
        ) as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload, headers=token_headers)

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "message": "Metadata rotation accepted.",
            "data": {"task_id": "123"},
        }

    def test_post_metadata_without_bootstrap(
        self, test_client, monkeypatch, token_headers
    ):
        url = "/api/v1/metadata/"

        mocked_check_metadata = pretend.call_recorder(lambda: False)
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.is_bootstrap_done",
            mocked_check_metadata,
        )

        with open(
            "tests/data_examples/metadata/update-root-payload.json"
        ) as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload, headers=token_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "detail": {"error": "Metadata rotation requires bootstrap done."}
        }

    def test_post_metadata_empty_payload(self, test_client, token_headers):
        url = "/api/v1/metadata/"

        response = test_client.post(url, json={}, headers=token_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "detail": [
                {
                    "loc": ["body", "metadata"],
                    "msg": "field required",
                    "type": "value_error.missing",
                },
            ]
        }

    def test_post_metadata_invalid_token(self, test_client, monkeypatch):
        url = "/api/v1/metadata/"

        token_headers = {"Authorization": "Bearer h4ck3r"}

        mocked_check_metadata = pretend.call_recorder(lambda: True)
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.is_bootstrap_done",
            mocked_check_metadata,
        )

        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.repository_metadata",
            mocked_repository_metadata,
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.get_task_id", lambda: "123"
        )

        with open(
            "tests/data_examples/metadata/update-root-payload.json"
        ) as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload, headers=token_headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "detail": {"error": "Failed to validate token"}
        }

    def test_post_metadata_incorrect_scope_token(
        self, test_client, monkeypatch
    ):
        token_url = "/api/v1/token/?expires=1"
        token_payload = {
            "username": "admin",
            "password": "secret",
            "scope": "write:bootstrap",
        }
        token = test_client.post(token_url, data=token_payload)
        token_headers = {
            "Authorization": f"Bearer {token.json()['access_token']}",
        }

        url = "/api/v1/metadata/"

        mocked_check_metadata = pretend.call_recorder(lambda: True)
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.is_bootstrap_done",
            mocked_check_metadata,
        )

        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.repository_metadata",
            mocked_repository_metadata,
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.get_task_id", lambda: "123"
        )

        with open(
            "tests/data_examples/metadata/update-root-payload.json"
        ) as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload, headers=token_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            "detail": {"error": "scope 'write:metadata' not allowed"}
        }

    def test_post_payload_incorrect_md_format(
        self, test_client, token_headers
    ):
        url = "/api/v1/metadata/"

        payload = {"metadata": {"timestamp": {}}}
        response = test_client.post(url, json=payload, headers=token_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json() == {
            "detail": [
                {
                    "loc": ["body", "metadata", "__key__"],
                    "msg": "unexpected value; permitted: 'root'",
                    "type": "value_error.const",
                    "ctx": {"given": "timestamp", "permitted": ["root"]},
                },
            ]
        }
