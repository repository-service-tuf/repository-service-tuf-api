# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json

import pretend
from fastapi import status


class TestGetBootstrap:
    def test_get_bootstrap_available(
        self, test_client, token_headers, monkeypatch
    ):
        url = "/api/v1/bootstrap/"
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state=None, task_id=None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.bootstrap_state",
            mocked_bootstrap_state,
        )

        response = test_client.get(url, headers=token_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "data": {"bootstrap": False},
            "message": "System available for bootstrap.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_get_bootstrap_not_available(
        self, test_client, monkeypatch, token_headers
    ):
        url = "/api/v1/bootstrap/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=True, state="finished", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.bootstrap_state",
            mocked_bootstrap_state,
        )

        response = test_client.get(url, headers=token_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "data": {"bootstrap": True, "state": "finished"},
            "message": "System LOCKED for bootstrap.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_get_bootstrap_invalid_token(self, test_client):
        url = "/api/v1/bootstrap/"

        token_headers = {"Authorization": "Bearer h4ck3r"}
        response = test_client.get(url, headers=token_headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "detail": {"error": "Failed to validate token"}
        }

    def test_get_bootstrap_incorrect_scope_token(self, test_client):
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
        url = "/api/v1/bootstrap/"

        response = test_client.get(url, headers=token_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            "detail": {"error": "scope 'read:bootstrap' not allowed"}
        }


class TestPostBootstrap:
    def test_post_bootstrap(self, test_client, monkeypatch, token_headers):
        url = "/api/v1/bootstrap/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.bootstrap_state",
            mocked_bootstrap_state,
        )
        mocked_async_result = pretend.stub(state="SUCCESS")
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None),
            AsyncResult=pretend.call_recorder(lambda *a: mocked_async_result),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.repository_metadata",
            mocked_repository_metadata,
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.get_task_id", lambda: "123"
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.pre_lock_bootstrap",
            lambda *a: None,
        )
        mocked__check_bootstrap_status = pretend.call_recorder(lambda *a: None)
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap._check_bootstrap_status",
            mocked__check_bootstrap_status,
        )

        with open("tests/data_examples/bootstrap/payload.json") as f:
            f_data = f.read()
        payload = json.loads(f_data)

        response = test_client.post(url, json=payload, headers=token_headers)

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "message": "Bootstrap accepted.",
            "data": {"task_id": "123"},
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked__check_bootstrap_status.calls == [
            pretend.call(task_id="123", timeout=300)
        ]

    def test_post_bootstrap_custom_timeout(
        self, test_client, monkeypatch, token_headers
    ):
        url = "/api/v1/bootstrap/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.bootstrap_state",
            mocked_bootstrap_state,
        )
        mocked_async_result = pretend.stub(state="SUCCESS")
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None),
            AsyncResult=pretend.call_recorder(lambda *a: mocked_async_result),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.repository_metadata",
            mocked_repository_metadata,
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.get_task_id", lambda: "123"
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.pre_lock_bootstrap",
            lambda *a: None,
        )
        mocked__check_bootstrap_status = pretend.call_recorder(lambda *a: None)
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap._check_bootstrap_status",
            mocked__check_bootstrap_status,
        )

        with open("tests/data_examples/bootstrap/payload.json") as f:
            f_data = f.read()
        payload = json.loads(f_data)
        payload["timeout"] = 600

        response = test_client.post(url, json=payload, headers=token_headers)

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "message": "Bootstrap accepted.",
            "data": {"task_id": "123"},
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked__check_bootstrap_status.calls == [
            pretend.call(task_id="123", timeout=600)
        ]

    def test_post_bootstrap_already_bootstrap(
        self, test_client, monkeypatch, token_headers
    ):
        url = "/api/v1/bootstrap/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=True, state="finished", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.bootstrap_state",
            mocked_bootstrap_state,
        )
        with open("tests/data_examples/bootstrap/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload, headers=token_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "detail": {
                "error": "System already has a Metadata. State: finished"
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_bootstrap_already_bootstrap_in_pre(
        self, test_client, monkeypatch, token_headers
    ):
        url = "/api/v1/bootstrap/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=True, state="pre", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.bootstrap_state",
            mocked_bootstrap_state,
        )
        with open("tests/data_examples/bootstrap/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload, headers=token_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "detail": {"error": "System already has a Metadata. State: pre"}
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_bootstrap_already_bootstrap_in_signing(
        self, test_client, monkeypatch, token_headers
    ):
        url = "/api/v1/bootstrap/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=True, state="signing", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.bootstrap.bootstrap_state",
            mocked_bootstrap_state,
        )
        with open("tests/data_examples/bootstrap/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload, headers=token_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "detail": {
                "error": "System already has a Metadata. State: signing"
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_bootstrap_empty_payload(self, test_client, token_headers):
        url = "/api/v1/bootstrap/"

        response = test_client.post(url, json={}, headers=token_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.url == f"{test_client.base_url}{url}"
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

    def test_post_bootstrap_invalid_token(self, test_client, monkeypatch):
        url = "/api/v1/bootstrap/"

        token_headers = {"Authorization": "Bearer h4ck3r"}

        with open("tests/data_examples/bootstrap/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload, headers=token_headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "detail": {"error": "Failed to validate token"}
        }

    def test_post_bootstrap_incorrect_scope_token(
        self, test_client, monkeypatch
    ):
        token_url = "/api/v1/token/?expires=1"
        token_payload = {
            "username": "admin",
            "password": "secret",
            "scope": "read:bootstrap",
        }
        token = test_client.post(token_url, data=token_payload)
        token_headers = {
            "Authorization": f"Bearer {token.json()['access_token']}",
        }

        url = "/api/v1/bootstrap/"

        with open("tests/data_examples/bootstrap/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload, headers=token_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            "detail": {"error": "scope 'write:bootstrap' not allowed"}
        }

    def test_post_payload_incorrect_md_format(
        self, test_client, token_headers
    ):
        url = "/api/v1/bootstrap/"

        payload = {"settings": {}, "metadata": {"timestamp": {}}}
        response = test_client.post(url, json=payload, headers=token_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json() == {
            "detail": [
                {
                    "loc": ["body", "settings", "expiration"],
                    "msg": "field required",
                    "type": "value_error.missing",
                },
                {
                    "loc": ["body", "settings", "services"],
                    "msg": "field required",
                    "type": "value_error.missing",
                },
                {
                    "loc": ["body", "metadata", "__key__"],
                    "msg": "unexpected value; permitted: 'root'",
                    "type": "value_error.const",
                    "ctx": {"given": "timestamp", "permitted": ["root"]},
                },
            ]
        }
