# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import copy
import json
from datetime import timezone

import pretend
from fastapi import status

import repository_service_tuf_api.common_models as common_models

METADATA_URL = "/api/v1/metadata/"
METADATA_ONLINE_URL = "/api/v1/metadata/online"
SIGN_URL = "/api/v1/metadata/sign/"
DELETE_SIGN_URL = "/api/v1/metadata/sign/delete"
MOCK_PATH = "repository_service_tuf_api.metadata"


class TestPostMetadata:
    def test_post_metadata(self, test_client, monkeypatch, fake_datetime):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        mocked_async_result = pretend.stub(state="SUCCESS")
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None),
            AsyncResult=pretend.call_recorder(lambda *a: mocked_async_result),
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata", mocked_repository_metadata
        )
        monkeypatch.setattr(f"{MOCK_PATH}.get_task_id", lambda: "123")
        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)
        with open(
            "tests/data_examples/metadata/update-root-payload.json"
        ) as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(METADATA_URL, json=payload)

        assert fake_datetime.now.calls == [pretend.call(timezone.utc)]
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.url == f"{test_client.base_url}{METADATA_URL}"
        assert response.json() == {
            "message": "Metadata update accepted.",
            "data": {"task_id": "123", "last_update": "2019-06-16T09:05:01Z"},
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_metadata_without_bootstrap(self, test_client, monkeypatch):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state=None)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        with open(
            "tests/data_examples/metadata/update-root-payload.json"
        ) as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(METADATA_URL, json=payload)

        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.url == f"{test_client.base_url}{METADATA_URL}"
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
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state="signing")
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        with open(
            "tests/data_examples/metadata/update-root-payload.json"
        ) as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(METADATA_URL, json=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{METADATA_URL}"
        assert response.json() == {
            "detail": {
                "message": "Task not accepted.",
                "error": "Requires bootstrap finished. State: signing",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_metadata_empty_payload(self, test_client):
        response = test_client.post(METADATA_URL, json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.url == f"{test_client.base_url}{METADATA_URL}"
        assert response.json() == {
            "detail": [
                {
                    "type": "missing",
                    "loc": ["body", "metadata"],
                    "msg": "Field required",
                    "input": {},
                    "url": "https://errors.pydantic.dev/2.6/v/missing",
                }
            ]
        }

    def test_post_payload_incorrect_metadata_format(self, test_client):
        payload = {"metadata": {"timestamp": {}}}
        response = test_client.post(METADATA_URL, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert {
            "detail": [
                {
                    "type": "literal_error",
                    "loc": ["body", "metadata", "timestamp", "[key]"],
                    "msg": "Input should be 'root'",
                    "input": "timestamp",
                    "ctx": {"expected": "'root'"},
                    "url": "https://errors.pydantic.dev/2.6/v/literal_error",
                },
                {
                    "type": "missing",
                    "loc": ["body", "metadata", "timestamp", "signatures"],
                    "msg": "Field required",
                    "input": {},
                    "url": "https://errors.pydantic.dev/2.6/v/missing",
                },
                {
                    "type": "missing",
                    "loc": ["body", "metadata", "timestamp", "signed"],
                    "msg": "Field required",
                    "input": {},
                    "url": "https://errors.pydantic.dev/2.6/v/missing",
                },
            ]
        } == response.json()


class TestPostMetadataOnline:
    def test_post_metadata_online(self, test_client, monkeypatch):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda: pretend.stub(bootstrap=True, state="ab123")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )

        def fake_get_fresh(setting: str) -> bool:
            if setting == "TARGETS_ONLINE_KEY":
                return True
            elif setting == "NUMBER_OF_DELEGATED_BINS":
                return False

        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda a: fake_get_fresh(a)),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.settings_repository",
            mocked_settings_repository,
        )
        fake_id = "fake_id"
        fake_get_task_id = pretend.call_recorder(lambda: fake_id)
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.get_task_id",
            fake_get_task_id,
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
        payload = {"roles": ["snapshot", "targets"]}

        response = test_client.post(METADATA_ONLINE_URL, json=payload)
        assert response.status_code == status.HTTP_202_ACCEPTED, response.text
        assert response.json() == {
            "data": {
                "task_id": fake_id,
                "last_update": "2019-06-16T09:05:01",
            },
            "message": "Force online metadata update accepted.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_settings_repository.reload.calls == [
            pretend.call(),
            pretend.call(),
        ]
        assert mocked_settings_repository.get_fresh.calls == [
            pretend.call("TARGETS_ONLINE_KEY"),
            pretend.call("NUMBER_OF_DELEGATED_BINS"),
        ]
        assert fake_get_task_id.calls == [pretend.call()]
        assert fake_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "force_online_metadata_update",
                    "payload": payload,
                },
                task_id=fake_id,
                queue="metadata_repository",
                acks_late=True,
            )
        ]
        assert fake_datetime.now.calls == [pretend.call()]

    def test_post_metadata_online_empty_payload(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda: pretend.stub(bootstrap=True, state="ab123")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )

        def fake_get_fresh(setting: str) -> bool:
            if setting == "TARGETS_ONLINE_KEY":
                return True
            elif setting == "NUMBER_OF_DELEGATED_BINS":
                return False

        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda a: fake_get_fresh(a)),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.settings_repository",
            mocked_settings_repository,
        )
        fake_id = "fake_id"
        fake_get_task_id = pretend.call_recorder(lambda: fake_id)
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.get_task_id",
            fake_get_task_id,
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
        payload = {"roles": []}

        response = test_client.post(METADATA_ONLINE_URL, json=payload)
        assert response.status_code == status.HTTP_202_ACCEPTED, response.text
        assert response.json() == {
            "data": {
                "task_id": fake_id,
                "last_update": "2019-06-16T09:05:01",
            },
            "message": "Force online metadata update accepted.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_settings_repository.reload.calls == [
            pretend.call(),
            pretend.call(),
        ]
        assert mocked_settings_repository.get_fresh.calls == [
            pretend.call("TARGETS_ONLINE_KEY"),
            pretend.call("NUMBER_OF_DELEGATED_BINS"),
        ]
        assert fake_get_task_id.calls == [pretend.call()]
        expected_payload = {"roles": common_models.Roles.online_roles_values()}
        assert fake_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "force_online_metadata_update",
                    "payload": expected_payload,
                },
                task_id=fake_id,
                queue="metadata_repository",
                acks_late=True,
            )
        ]
        assert fake_datetime.now.calls == [pretend.call()]

    def test_post_metadata_online_bootstrap_not_ready(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda: pretend.stub(bootstrap=False, state="signing-")
        )
        payload = {"roles": ["snapshot", "targets"]}
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )

        response = test_client.post(METADATA_ONLINE_URL, json=payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "detail": {
                "message": "Task not accepted.",
                "error": "Requires bootstrap finished. State: signing-",
            },
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_metadata_online_targets_offline_role_cannot_update(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda: pretend.stub(bootstrap=True, state="ab123")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )
        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda a: False),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.settings_repository",
            mocked_settings_repository,
        )
        payload = {"roles": ["snapshot", "targets"]}

        response = test_client.post(METADATA_ONLINE_URL, json=payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        err_msg = "Targets is an offline role - use other endpoint to update"
        assert response.json() == {
            "detail": {
                "message": "Task not accepted.",
                "error": err_msg,
            },
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_settings_repository.reload.calls == [pretend.call()]
        assert mocked_settings_repository.get_fresh.calls == [
            pretend.call("TARGETS_ONLINE_KEY")
        ]

    def test_post_metadata_online_bins_used_bad_payload(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda: pretend.stub(bootstrap=True, state="ab123")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.bootstrap_state",
            mocked_bootstrap_state,
        )
        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda a: True),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.metadata.settings_repository",
            mocked_settings_repository,
        )
        payload = {"roles": ["snapshot", "targets", "abcsdaw"]}

        response = test_client.post(METADATA_ONLINE_URL, json=payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        roles = common_models.Roles.all_str()
        err_msg = (
            f"Hash bin delegation is used and only {roles} roles can be bumped"
        )
        assert response.json() == {
            "detail": {
                "message": "Task not accepted.",
                "error": err_msg,
            },
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_settings_repository.reload.calls == [
            pretend.call(),
            pretend.call(),
        ]
        assert mocked_settings_repository.get_fresh.calls == [
            pretend.call("TARGETS_ONLINE_KEY"),
            pretend.call("NUMBER_OF_DELEGATED_BINS"),
        ]


class TestGetMetadataSign:
    def test_get_metadata_sign(self, test_client, monkeypatch):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True, state="signing")
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        with open("tests/data_examples/bootstrap/payload_bins.json") as f:
            md_content = f.read()
        metadata_data = json.loads(md_content)
        fake_metadata = pretend.stub(
            to_dict=pretend.call_recorder(
                lambda: metadata_data["metadata"]["root"]
            )
        )

        def get_role(role_setting: str):
            if role_setting == "ROOT_SIGNING":
                return fake_metadata
            return None

        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get=pretend.call_recorder(lambda a: get_role(a)),
            ROOT_SIGNING=fake_metadata,
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.settings_repository", mocked_settings_repository
        )

        response = test_client.get(SIGN_URL)
        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "data": {"metadata": {"root": metadata_data["metadata"]["root"]}},
            "message": "Metadata role(s) pending signing",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_settings_repository.reload.calls == [pretend.call()]
        assert mocked_settings_repository.get.calls == [
            pretend.call("ROOT_SIGNING"),
            pretend.call("TRUSTED_ROOT"),
        ]
        assert fake_metadata.to_dict.calls == [pretend.call()]

    def test_get_metadata_sign_with_trusted_root(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True, state="signing")
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        with open("tests/data_examples/bootstrap/payload_bins.json") as f:
            md_content = f.read()

        metadata_data = json.loads(md_content)
        fake_metadata = pretend.stub(
            to_dict=pretend.call_recorder(
                lambda: metadata_data["metadata"]["root"]
            )
        )
        # Change trusted root:
        trusted_root_dict = copy.deepcopy(metadata_data["metadata"]["root"])
        trusted_root_dict["signed"]["version"] = 10
        fake_trusted_metadata = pretend.stub(
            to_dict=pretend.call_recorder(lambda: trusted_root_dict)
        )

        def get_role(setting: str):
            if setting == "ROOT_SIGNING":
                return fake_metadata
            elif setting == "TRUSTED_ROOT":
                return fake_trusted_metadata

        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get=pretend.call_recorder(lambda a: get_role(a)),
            ROOT_SIGNING=fake_metadata,
            TRUSTED_ROOT=fake_metadata,
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.settings_repository", mocked_settings_repository
        )

        response = test_client.get(SIGN_URL)
        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "data": {
                "metadata": {
                    "root": metadata_data["metadata"]["root"],
                    "trusted_root": trusted_root_dict,
                }
            },
            "message": "Metadata role(s) pending signing",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_settings_repository.reload.calls == [pretend.call()]
        assert mocked_settings_repository.get.calls == [
            pretend.call("ROOT_SIGNING"),
            pretend.call("TRUSTED_ROOT"),
        ]
        assert fake_metadata.to_dict.calls == [pretend.call()]
        assert fake_trusted_metadata.to_dict.calls == [pretend.call()]

    def test_get_metadata_sign_no_pending_roles(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True, state="signing")
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )

        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.settings_repository", mocked_settings_repository
        )

        response = test_client.get(SIGN_URL)
        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "message": "No metadata pending signing available",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_settings_repository.reload.calls == [pretend.call()]

    def test_get_metadata_sign_no_bootstrap(self, test_client, monkeypatch):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state=None)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        response = test_client.get(SIGN_URL)

        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "detail": {
                "message": "No metadata pending signing available",
                "error": "Requires bootstrap started. State: None",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_get_metadata_sign_bootstrap_pre(self, test_client, monkeypatch):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state="pre")
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        response = test_client.get(SIGN_URL)

        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "detail": {
                "message": "No metadata pending signing available",
                "error": "Requires bootstrap started. State: pre",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]


class TestPostMetadataSign:
    def test_post_metadata_sign(self, test_client, monkeypatch, fake_datetime):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True, state="signing")
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        monkeypatch.setattr(f"{MOCK_PATH}.get_task_id", lambda: "fake_id")
        fake_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata", fake_repository_metadata
        )
        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)
        payload = {"role": "root", "signature": {"keyid": "k1", "sig": "s1"}}

        response = test_client.post(SIGN_URL, json=payload)
        assert fake_datetime.now.calls == [pretend.call(timezone.utc)]
        assert response.status_code == status.HTTP_202_ACCEPTED, response.text
        assert response.json() == {
            "data": {
                "task_id": "fake_id",
                "last_update": "2019-06-16T09:05:01Z",
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
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state=None)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        payload = {"role": "root", "signature": {"keyid": "k1", "sig": "s1"}}

        response = test_client.post(SIGN_URL, json=payload)
        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json() == {
            "detail": {
                "message": "No signing pending.",
                "error": "Requires bootstrap in signing state. State: None",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_metadata_bootstrap_finished(self, test_client, monkeypatch):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state="finished")
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        payload = {"role": "root", "signature": {"keyid": "k1", "sig": "s1"}}

        response = test_client.post(SIGN_URL, json=payload)
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
    def test_post_metadata_sign_delete(
        self, test_client, monkeypatch, fake_datetime
    ):
        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: "metadata"),
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.settings_repository", mocked_settings_repository
        )
        fake_get_task_id = pretend.call_recorder(lambda: "123")
        monkeypatch.setattr(f"{MOCK_PATH}.get_task_id", fake_get_task_id)
        mocked_async_result = pretend.stub(state="SUCCESS")
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None),
            AsyncResult=pretend.call_recorder(lambda *a: mocked_async_result),
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata", mocked_repository_metadata
        )
        payload = {"role": "root"}
        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)

        response = test_client.post(DELETE_SIGN_URL, json=payload)
        assert fake_datetime.now.calls == [pretend.call(timezone.utc)]
        assert response.status_code == status.HTTP_202_ACCEPTED, response.text
        assert response.json() == {
            "data": {"task_id": "123", "last_update": "2019-06-16T09:05:01Z"},
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
        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: None),
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.settings_repository", mocked_settings_repository
        )

        payload = {"role": "root"}

        response = test_client.post(DELETE_SIGN_URL, json=payload)
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
