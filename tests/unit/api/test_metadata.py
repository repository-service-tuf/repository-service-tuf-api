# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import datetime
import json

import pretend
from fastapi import status


class TestPostMetadata:
    def test_post_metadata(self, test_client, monkeypatch):
        url = "/api/v1/metadata/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
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
        fake_time = datetime.datetime(2019, 6, 16, 9, 5, 1)
        fake_datetime = pretend.stub(
            now=pretend.call_recorder(lambda: fake_time)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.datetime", fake_datetime
        )
        with open(
            "tests/data_examples/metadata/update-root-payload.json"
        ) as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload)

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "message": "Metadata update accepted.",
            "data": {"task_id": "123", "last_update": "2019-06-16T09:05:01"},
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_metadata_without_bootstrap(self, test_client, monkeypatch):
        url = "/api/v1/metadata/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state=None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )
        with open(
            "tests/data_examples/metadata/update-root-payload.json"
        ) as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "detail": {
                "message": "Task not accepted.",
                "error": "Requires bootstrap finished. State: None",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_metadata_bootstrap_intermediate_state(
        self, test_client, monkeypatch
    ):
        url = "/api/v1/metadata/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state="signing")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )
        with open(
            "tests/data_examples/metadata/update-root-payload.json"
        ) as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(url, json=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{url}"
        assert response.json() == {
            "detail": {
                "message": "Task not accepted.",
                "error": "Requires bootstrap finished. State: signing",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_metadata_empty_payload(self, test_client):
        url = "/api/v1/metadata/"

        response = test_client.post(url, json={})

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

    def test_post_payload_incorrect_md_format(self, test_client):
        url = "/api/v1/metadata/"

        payload = {"metadata": {"timestamp": {}}}
        response = test_client.post(url, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert {
            "loc": ["body", "metadata", "__key__"],
            "msg": "unexpected value; permitted: 'root'",
            "type": "value_error.const",
            "ctx": {"given": "timestamp", "permitted": ["root"]},
        } in response.json()["detail"]


class TestGetMetadataSign:
    def test_get_metadata_sign(self, test_client, monkeypatch):
        url = "/api/v1/metadata/sign/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True, state="signing")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )
        with open("tests/data_examples/bootstrap/payload.json") as f:
            md_content = f.read()
        metadata_data = json.loads(md_content)
        fake_metadata = pretend.stub(
            to_dict=pretend.call_recorder(
                lambda: metadata_data["metadata"]["root"]
            )
        )
        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get=pretend.call_recorder(lambda *a: fake_metadata),
            ROOT_SIGNING=fake_metadata,
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.settings_repository",
            mocked_settings_repository,
        )

        response = test_client.get(url)
        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "data": {"metadata": {"root": metadata_data["metadata"]["root"]}},
            "message": "Metadata role(s) pending signing",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_settings_repository.reload.calls == [pretend.call()]
        assert mocked_settings_repository.get.calls == [
            pretend.call("ROOT_SIGNING")
        ]
        assert fake_metadata.to_dict.calls == [pretend.call()]

    def test_get_metadata_sign_no_bootstrap(self, test_client, monkeypatch):
        url = "/api/v1/metadata/sign/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state=None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )
        response = test_client.get(url)

        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "detail": {
                "message": "No signing available",
                "error": "Requires bootstrap started. State: None",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_get_metadata_sign_bootstrap_pre(self, test_client, monkeypatch):
        url = "/api/v1/metadata/sign/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state="pre")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )
        response = test_client.get(url)

        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "detail": {
                "message": "No signing available",
                "error": "Requires bootstrap started. State: pre",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]


class TestPostMetadataSign:
    def test_post_metadata_sign(self, test_client, monkeypatch):
        url = "/api/v1/metadata/sign/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True, state="signing")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.get_task_id",
            lambda: "fake_id",
        )
        fake_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.repository_metadata",
            fake_repository_metadata,
        )
        fake_time = datetime.datetime(2019, 6, 16, 9, 5, 1)
        fake_datetime = pretend.stub(
            now=pretend.call_recorder(lambda: fake_time)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.datetime", fake_datetime
        )
        payload = {"role": "root", "signature": {"keyid": "k1", "sig": "s1"}}

        response = test_client.post(url, json=payload)
        assert response.status_code == status.HTTP_202_ACCEPTED, response.text
        assert response.json() == {
            "data": {
                "task_id": "fake_id",
                "last_update": "2019-06-16T09:05:01",
            },
            "message": "Metadata sign accepted.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert fake_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "sign_metadata",
                    "payload": {
                        "role": "root",
                        "signature": {"keyid": "k1", "sig": "s1"},
                    },
                },
                task_id="fake_id",
                queue="metadata_repository",
                acks_late=True,
            )
        ]

    def test_post_metadata_no_bootstrap(self, test_client, monkeypatch):
        url = "/api/v1/metadata/sign/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state=None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )
        payload = {"role": "root", "signature": {"keyid": "k1", "sig": "s1"}}

        response = test_client.post(url, json=payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "detail": {
                "message": "No signing pending.",
                "error": "Requires bootstrap in signing state. State: None",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_metadata_bootstrap_finished(self, test_client, monkeypatch):
        url = "/api/v1/metadata/sign/"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state="finished")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )
        payload = {"role": "root", "signature": {"keyid": "k1", "sig": "s1"}}

        response = test_client.post(url, json=payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "detail": {
                "message": "No signing pending.",
                "error": (
                    "Requires bootstrap in signing state. State: finished"
                ),
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]


class TestPostMetadataSignDelete:
    def test_post_metadata_sign_delete(self, test_client, monkeypatch):
        url = "/api/v1/metadata/sign/delete"
        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: "metadata"),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.settings_repository",
            mocked_settings_repository,
        )
        fake_get_task_id = pretend.call_recorder(lambda: "123")
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.get_task_id", fake_get_task_id
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
        payload = {"role": "root"}
        fake_time = datetime.datetime(2019, 6, 16, 9, 5, 1)
        fake_datetime = pretend.stub(
            now=pretend.call_recorder(lambda: fake_time)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.datetime", fake_datetime
        )

        response = test_client.post(url, json=payload)
        assert response.status_code == status.HTTP_202_ACCEPTED, response.text
        assert response.json() == {
            "data": {"task_id": "123", "last_update": "2019-06-16T09:05:01"},
            "message": "Metadata sign delete accepted.",
        }
        assert mocked_settings_repository.reload.calls == [pretend.call()]
        assert mocked_settings_repository.get_fresh.calls == [
            pretend.call("ROOT_SIGNING")
        ]
        assert fake_get_task_id.calls == [pretend.call()]
        assert mocked_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "delete_sign_metadata",
                    "payload": {"role": "root"},
                },
                task_id="123",
                queue="metadata_repository",
                acks_late=True,
            )
        ]

    def test_metadata_sign_delete_role_not_in_signing_status(
        self, test_client, monkeypatch
    ):
        url = "/api/v1/metadata/sign/delete"
        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: None),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.settings_repository",
            mocked_settings_repository,
        )

        payload = {"role": "root"}

        response = test_client.post(url, json=payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "detail": {
                "message": "No signing process for root.",
                "error": "The root role is not in a signing process.",
            }
        }
        assert mocked_settings_repository.reload.calls == [pretend.call()]
        assert mocked_settings_repository.get_fresh.calls == [
            pretend.call("ROOT_SIGNING")
        ]
