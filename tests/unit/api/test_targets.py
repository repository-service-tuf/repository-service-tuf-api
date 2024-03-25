# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
import datetime
import json
from uuid import uuid4

import pretend
from fastapi import status

ARTIFACTS_URL = "/api/v1/artifacts/"
ARTIFACTS_DELETE_URL = "/api/v1/artifacts/delete"
ARTIFACTS_POST_URL = "/api/v1/artifacts/publish/"


class TestPostArtifacts:
    def test_post(self, monkeypatch, test_client):
        with open("tests/data_examples/artifacts/add_payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.bootstrap_state",
            mocked_bootstrap_state,
        )
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda **kw: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.repository_metadata",
            mocked_repository_metadata,
        )
        fake_task_id = uuid4().hex
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.get_task_id",
            lambda: fake_task_id,
        )
        fake_time = datetime.datetime(2019, 6, 16, 9, 5, 1)
        fake_datetime = pretend.stub(
            now=pretend.call_recorder(lambda: fake_time)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.datetime", fake_datetime
        )
        response = test_client.post(ARTIFACTS_URL, json=payload)
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "data": {
                "artifacts": ["file1.tar.gz", "file2.tar.gz", "file3.tar.gz"],
                "task_id": fake_task_id,
                "last_update": "2019-06-16T09:05:01",
            },
            "message": "New Artifact(s) successfully submitted.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "add_artifacts",
                    "payload": {
                        **payload,
                        "publish_artifacts": True,
                        "add_task_id_to_custom": False,
                    },
                },
                task_id=fake_task_id,
                queue="metadata_repository",
                acks_late=True,
            )
        ]

    def test_post_with_add_task_id_to_custom(self, monkeypatch, test_client):
        with open("tests/data_examples/artifacts/add_payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.bootstrap_state",
            mocked_bootstrap_state,
        )
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda **kw: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.repository_metadata",
            mocked_repository_metadata,
        )
        fake_task_id = uuid4().hex
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.get_task_id",
            lambda: fake_task_id,
        )
        fake_time = datetime.datetime(2019, 6, 16, 9, 5, 1)
        fake_datetime = pretend.stub(
            now=pretend.call_recorder(lambda: fake_time)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.datetime", fake_datetime
        )

        # enable to add task id to custom metadata field
        payload["add_task_id_to_custom"] = True

        response = test_client.post(ARTIFACTS_URL, json=payload)
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "data": {
                "artifacts": ["file1.tar.gz", "file2.tar.gz", "file3.tar.gz"],
                "task_id": fake_task_id,
                "last_update": "2019-06-16T09:05:01",
            },
            "message": "New Artifact(s) successfully submitted.",
        }

        # Add task_id info into custom as it will be done in the post function
        for artifact in payload["artifacts"]:
            if artifact["info"].get("custom") is None:
                artifact["info"]["custom"] = {}

            # Add task_id info in custom while keeping the old custom
            artifact["info"]["custom"] = {
                "added_by_task_id": fake_task_id,
                **artifact["info"]["custom"],
            }

        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "add_artifacts",
                    "payload": {
                        **payload,
                        "publish_artifacts": True,
                    },
                },
                task_id=fake_task_id,
                queue="metadata_repository",
                acks_late=True,
            )
        ]

    def test_post_publish_artifacts_false(self, monkeypatch, test_client):
        with open("tests/data_examples/artifacts/add_payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)

        # Disable publish_artifacts
        payload["publish_artifacts"] = False

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.bootstrap_state",
            mocked_bootstrap_state,
        )
        fake_task_id = uuid4().hex
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.get_task_id",
            lambda: fake_task_id,
        )
        fake_time = datetime.datetime(2019, 6, 16, 9, 5, 1)
        fake_datetime = pretend.stub(
            now=pretend.call_recorder(lambda: fake_time)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.datetime", fake_datetime
        )
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda **kw: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.repository_metadata",
            mocked_repository_metadata,
        )
        response = test_client.post(ARTIFACTS_URL, json=payload)
        assert response.status_code == status.HTTP_202_ACCEPTED
        msg = (
            "New Artifact(s) successfully submitted. "
            "Publishing will be skipped."
        )
        assert response.json() == {
            "data": {
                "artifacts": ["file1.tar.gz", "file2.tar.gz", "file3.tar.gz"],
                "task_id": fake_task_id,
                "last_update": "2019-06-16T09:05:01",
            },
            "message": msg,
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "add_artifacts",
                    "payload": {**payload, "add_task_id_to_custom": False},
                },
                task_id=fake_task_id,
                queue="metadata_repository",
                acks_late=True,
            )
        ]

    def test_post_without_bootstrap(self, monkeypatch, test_client):
        with open("tests/data_examples/artifacts/add_payload.json") as f:
            f_data = f.read()

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state=None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.bootstrap_state",
            mocked_bootstrap_state,
        )

        payload = json.loads(f_data)

        response = test_client.post(ARTIFACTS_URL, json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "detail": {
                "message": "Task not accepted.",
                "error": "It requires bootstrap finished. State: None",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_with_bootstrap_intermediate_state(
        self, monkeypatch, test_client
    ):
        with open("tests/data_examples/artifacts/add_payload.json") as f:
            f_data = f.read()

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state="signing")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.bootstrap_state",
            mocked_bootstrap_state,
        )

        payload = json.loads(f_data)

        response = test_client.post(ARTIFACTS_URL, json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "detail": {
                "message": "Task not accepted.",
                "error": "It requires bootstrap finished. State: signing",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_missing_required_field(self, test_client):
        payload = {
            "artifacts": [
                {
                    "info": {
                        "length": 11342,
                        "custom": {"key": "value"},
                    },
                }
            ]
        }

        response = test_client.post(ARTIFACTS_URL, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPostArtifactsDelete:
    def test_post_delete(self, monkeypatch, test_client):
        payload = {
            "artifacts": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"],
        }

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.bootstrap_state",
            mocked_bootstrap_state,
        )
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda **kw: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.repository_metadata",
            mocked_repository_metadata,
        )
        fake_task_id = uuid4().hex
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.get_task_id",
            lambda: fake_task_id,
        )
        fake_time = datetime.datetime(2019, 6, 16, 9, 5, 1)
        fake_datetime = pretend.stub(
            now=pretend.call_recorder(lambda: fake_time)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.datetime", fake_datetime
        )

        response = test_client.post(ARTIFACTS_DELETE_URL, json=payload)

        assert fake_datetime.now.calls == [pretend.call()]
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "data": {
                "artifacts": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"],
                "task_id": fake_task_id,
                "last_update": "2019-06-16T09:05:01",
            },
            "message": "Remove Artifact(s) successfully submitted.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "remove_artifacts",
                    "payload": {**payload, "publish_artifacts": True},
                },
                task_id=fake_task_id,
                queue="metadata_repository",
                acks_late=True,
            )
        ]

    def test_post_publish_artifacts_delete_false(
        self, monkeypatch, test_client
    ):
        payload = {
            "artifacts": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"],
            "publish_artifacts": False,
        }

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.bootstrap_state",
            mocked_bootstrap_state,
        )
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda **kw: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.repository_metadata",
            mocked_repository_metadata,
        )
        fake_task_id = uuid4().hex
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.get_task_id",
            lambda: fake_task_id,
        )
        fake_time = datetime.datetime(2019, 6, 16, 9, 5, 1)
        fake_datetime = pretend.stub(
            now=pretend.call_recorder(lambda: fake_time)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.datetime", fake_datetime
        )

        response = test_client.post(ARTIFACTS_DELETE_URL, json=payload)

        assert response.status_code == status.HTTP_202_ACCEPTED
        msg = (
            "Remove Artifact(s) successfully submitted. "
            + "Publishing will be skipped."
        )
        assert response.json() == {
            "data": {
                "artifacts": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"],
                "task_id": fake_task_id,
                "last_update": "2019-06-16T09:05:01",
            },
            "message": msg,
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "remove_artifacts",
                    "payload": payload,
                },
                task_id=fake_task_id,
                queue="metadata_repository",
                acks_late=True,
            )
        ]

    def test_post_without_bootstrap_delete(self, monkeypatch, test_client):
        payload = {
            "artifacts": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"]
        }
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state=None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.bootstrap_state",
            mocked_bootstrap_state,
        )
        response = test_client.post(ARTIFACTS_DELETE_URL, json=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "detail": {
                "message": "Task not accepted.",
                "error": "It requires bootstrap finished. State: None",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_with_bootstrap_intermediate_state_delete(
        self, monkeypatch, test_client
    ):
        payload = {
            "artifacts": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"]
        }
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state="signing")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.bootstrap_state",
            mocked_bootstrap_state,
        )
        response = test_client.post(ARTIFACTS_DELETE_URL, json=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "detail": {
                "message": "Task not accepted.",
                "error": "It requires bootstrap finished. State: signing",
            }
        }

    def test_post_missing_required_field_delete(self, test_client):
        payload = {"paths": ["file-v1.0.0_i683.tar.gz", "v0.4.1/file.tar.gz"]}

        response = test_client.post(ARTIFACTS_DELETE_URL, json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPostArtifactsPublish:
    def test_post_publish(self, monkeypatch, test_client):
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda **kw: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.repository_metadata",
            mocked_repository_metadata,
        )
        fake_task_id = uuid4().hex
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.get_task_id",
            lambda: fake_task_id,
        )
        fake_time = datetime.datetime(2019, 6, 16, 9, 5, 1)
        fake_datetime = pretend.stub(
            now=pretend.call_recorder(lambda: fake_time)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.artifacts.datetime", fake_datetime
        )
        response = test_client.post(ARTIFACTS_POST_URL)
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "data": {
                "artifacts": [],
                "task_id": fake_task_id,
                "last_update": "2019-06-16T09:05:01",
            },
            "message": "Publish artifacts successfully submitted.",
        }
        assert mocked_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "publish_artifacts",
                    "payload": None,
                },
                task_id=fake_task_id,
                queue="rstuf_internals",
                acks_late=True,
            )
        ]
