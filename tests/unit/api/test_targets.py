# SPDX-FileCopyrightText: 2022 VMware Inc
#
# SPDX-License-Identifier: MIT
import datetime
import json
from uuid import uuid4

import pretend
from fastapi import status


class TestPostTargets:
    def test_post(self, monkeypatch, test_client, token_headers):
        url = "/api/v1/targets/"
        with open("tests/data_examples/targets/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.targets.is_bootstrap_done",
            lambda: True,
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.targets.repository_metadata",
            mocked_repository_metadata,
        )
        fake_task_id = uuid4().hex
        monkeypatch.setattr(
            "repository_service_tuf_api.targets.get_task_id",
            lambda: fake_task_id,
        )
        fake_time = datetime.datetime(2019, 6, 16, 9, 5, 1)
        fake_datetime = pretend.stub(
            now=pretend.call_recorder(lambda: fake_time)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.targets.datetime", fake_datetime
        )
        response = test_client.post(url, json=payload, headers=token_headers)
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "data": {
                "targets": ["file1.tar.gz", "file2.tar.gz"],
                "task_id": fake_task_id,
                "last_update": "2019-06-16T09:05:01",
            },
            "message": "Target(s) successfully submitted.",
        }
        assert mocked_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "add_targets",
                    "payload": payload,
                },
                task_id=fake_task_id,
                queue="metadata_repository",
                acks_late=True,
            )
        ]

    def test_post_without_bootstrap(
        self, monkeypatch, test_client, token_headers
    ):
        url = "/api/v1/targets/"
        with open("tests/data_examples/targets/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        monkeypatch.setattr(
            "repository_service_tuf_api.targets.is_bootstrap_done",
            lambda: False,
        )
        response = test_client.post(url, json=payload, headers=token_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "detail": {"error": "System has not a Repository Metadata"}
        }

    def test_post_missing_required_field(self, test_client, token_headers):
        url = "/api/v1/targets/"
        payload = {
            "targets": [
                {
                    "info": {
                        "length": 11342,
                        "custom": {"key": "value"},
                    },
                }
            ]
        }

        response = test_client.post(url, json=payload, headers=token_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_post_unauthorized_invalid_token(self, test_client):
        headers = {
            "Authorization": "Bearer 123456789abcef",
        }
        url = "/api/v1/targets/"
        with open("tests/data_examples/targets/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)

        response = test_client.post(url, json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "detail": {"error": "Failed to validate token"}
        }

    def test_post_forbidden_user_incorrect_scope_token(self, test_client):
        token_url = "/api/v1/token/?expires=1"
        token_payload = {
            "username": "admin",
            "password": "secret",
            "scope": "read:settings",
        }
        token = test_client.post(token_url, data=token_payload)
        headers = {
            "Authorization": f"Bearer {token.json()['access_token']}",
        }
        url = "/api/v1/targets/"
        with open("tests/data_examples/targets/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)

        response = test_client.post(url, json=payload, headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            "detail": {"error": "scope 'write:targets' not allowed"}
        }


class TestDeleteTargets:
    def test_delete(self, monkeypatch, test_client, token_headers):
        url = "/api/v1/targets/"

        payload = {
            "targets": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"]
        }

        monkeypatch.setattr(
            "repository_service_tuf_api.targets.is_bootstrap_done",
            lambda: True,
        )
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.targets.repository_metadata",
            mocked_repository_metadata,
        )
        fake_task_id = uuid4().hex
        monkeypatch.setattr(
            "repository_service_tuf_api.targets.get_task_id",
            lambda: fake_task_id,
        )
        fake_time = datetime.datetime(2019, 6, 16, 9, 5, 1)
        fake_datetime = pretend.stub(
            now=pretend.call_recorder(lambda: fake_time)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.targets.datetime", fake_datetime
        )

        response = test_client.delete(url, json=payload, headers=token_headers)
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "data": {
                "targets": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"],
                "task_id": fake_task_id,
                "last_update": "2019-06-16T09:05:01",
            },
            "message": "Remove Target(s) successfully submitted.",
        }
        assert mocked_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "remove_targets",
                    "payload": payload,
                },
                task_id=fake_task_id,
                queue="metadata_repository",
                acks_late=True,
            )
        ]

    def test_delete_without_bootstrap(
        self, monkeypatch, test_client, token_headers
    ):
        url = "/api/v1/targets/"

        payload = {
            "targets": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"]
        }
        monkeypatch.setattr(
            "repository_service_tuf_api.targets.is_bootstrap_done",
            lambda: False,
        )
        response = test_client.delete(url, json=payload, headers=token_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "detail": {"error": "System has not a Repository Metadata"}
        }

    def test_delete_missing_required_field(self, test_client, token_headers):
        url = "/api/v1/targets/"

        payload = {"paths": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"]}

        response = test_client.delete(url, json=payload, headers=token_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_unauthorized_invalid_token(self, test_client):
        headers = {
            "Authorization": "Bearer 123456789abcef",
        }
        url = "/api/v1/targets/"

        payload = {
            "targets": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"]
        }

        response = test_client.delete(url, json=payload, headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "detail": {"error": "Failed to validate token"}
        }

    def test_post_forbidden_user_incorrect_scope_token(self, test_client):
        token_url = "/api/v1/token/?expires=1"
        token_payload = {
            "username": "admin",
            "password": "secret",
            "scope": "write:targets",
        }
        token = test_client.post(token_url, data=token_payload)
        headers = {
            "Authorization": f"Bearer {token.json()['access_token']}",
        }
        url = "/api/v1/targets/"

        payload = {
            "targets": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"]
        }

        response = test_client.delete(url, json=payload, headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            "detail": {"error": "scope 'delete:targets' not allowed"}
        }
