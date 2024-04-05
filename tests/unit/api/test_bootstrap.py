# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
from datetime import timezone

import pretend
import pytest
from fastapi import status

BOOTSTRAP_URL = "/api/v1/bootstrap/"
MOCK_PATH = "repository_service_tuf_api.bootstrap"


class TestGetBootstrap:
    def test_get_bootstrap_available(self, test_client, monkeypatch):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state=None, task_id=None)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )

        response = test_client.get(BOOTSTRAP_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert response.json() == {
            "data": {"bootstrap": False},
            "message": "System available for bootstrap.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_get_bootstrap_not_available(self, test_client, monkeypatch):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=True, state="finished", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )

        response = test_client.get(BOOTSTRAP_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert response.json() == {
            "data": {"bootstrap": True, "state": "finished", "id": "task_id"},
            "message": "System LOCKED for bootstrap.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_get_bootstrap_already_bootstrap_in_pre(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="pre", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )

        response = test_client.get(BOOTSTRAP_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert response.json() == {
            "data": {"bootstrap": False, "state": "pre", "id": "task_id"},
            "message": "System LOCKED for bootstrap.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_get_bootstrap_already_bootstrap_in_signing(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="signing", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )

        response = test_client.get(BOOTSTRAP_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert response.json() == {
            "data": {"bootstrap": False, "state": "signing", "id": "task_id"},
            "message": "System LOCKED for bootstrap.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]


class TestPostBootstrap:
    def test_post_bootstrap_bins_delegation(
        self, test_client, monkeypatch, fake_datetime
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="finished", task_id="task_id"
            )
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
        monkeypatch.setattr(f"{MOCK_PATH}.pre_lock_bootstrap", lambda *a: None)
        mocked__check_bootstrap_status = pretend.call_recorder(lambda *a: None)

        monkeypatch.setattr(
            f"{MOCK_PATH}._check_bootstrap_status",
            mocked__check_bootstrap_status,
        )

        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)

        with open("tests/data_examples/bootstrap/payload_bins.json") as f:
            f_data = f.read()
        payload = json.loads(f_data)

        response = test_client.post(BOOTSTRAP_URL, json=payload)

        assert fake_datetime.now.calls == [pretend.call(timezone.utc)]
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert response.json() == {
            "message": "Bootstrap accepted.",
            "data": {"task_id": "123", "last_update": "2019-06-16T09:05:01Z"},
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked__check_bootstrap_status.calls == [
            pretend.call(task_id="123", timeout=300)
        ]

    def test_post_bootstrap_custom_delegation(
        self, test_client, monkeypatch, fake_datetime
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="finished", task_id="task_id"
            )
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
        monkeypatch.setattr(f"{MOCK_PATH}.pre_lock_bootstrap", lambda *a: None)
        mocked__check_bootstrap_status = pretend.call_recorder(lambda *a: None)
        monkeypatch.setattr(
            f"{MOCK_PATH}._check_bootstrap_status",
            mocked__check_bootstrap_status,
        )

        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)

        path = "tests/data_examples/bootstrap/payload_custom_targets.json"
        with open(path) as f:
            f_data = f.read()
        payload = json.loads(f_data)

        response = test_client.post(BOOTSTRAP_URL, json=payload)

        assert fake_datetime.now.calls == [pretend.call(timezone.utc)]
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert response.json() == {
            "message": "Bootstrap accepted.",
            "data": {"task_id": "123", "last_update": "2019-06-16T09:05:01Z"},
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked__check_bootstrap_status.calls == [
            pretend.call(task_id="123", timeout=300)
        ]

    def test_post_bootstrap_unrecognized_field(
        self, test_client, monkeypatch, fake_datetime
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="finished", task_id="task_id"
            )
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
        monkeypatch.setattr(f"{MOCK_PATH}.pre_lock_bootstrap", lambda *a: None)
        mocked__check_bootstrap_status = pretend.call_recorder(lambda *a: None)
        monkeypatch.setattr(
            f"{MOCK_PATH}._check_bootstrap_status",
            mocked__check_bootstrap_status,
        )

        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)

        with open("tests/data_examples/bootstrap/payload_bins.json") as f:
            f_data = f.read()
        payload = json.loads(f_data)
        payload["metadata"]["root"]["signed"]["x-v-n-url"] = "http://url.com"
        response = test_client.post(BOOTSTRAP_URL, json=payload)

        assert fake_datetime.now.calls == [pretend.call(timezone.utc)]
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert response.json() == {
            "message": "Bootstrap accepted.",
            "data": {"task_id": "123", "last_update": "2019-06-16T09:05:01Z"},
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked__check_bootstrap_status.calls == [
            pretend.call(task_id="123", timeout=300)
        ]

    def test_post_bootstrap_unrecognized_field_invalid(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="finished", task_id="task_id"
            )
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
        monkeypatch.setattr(f"{MOCK_PATH}.pre_lock_bootstrap", lambda *a: None)

        with open("tests/data_examples/bootstrap/payload_bins.json") as f:
            f_data = f.read()
        payload = json.loads(f_data)
        payload["metadata"]["root"]["signed"]["x-url"] = "http://example.com"

        response = test_client.post(BOOTSTRAP_URL, json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert (
            "unrecognized_field must use format x-<vendor>-<name>"
            in response.text
        )

    def test_post_bootstrap_unrecognized_field_must_start_with_x(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="finished", task_id="task_id"
            )
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
        monkeypatch.setattr(f"{MOCK_PATH}.pre_lock_bootstrap", lambda *a: None)

        with open("tests/data_examples/bootstrap/payload_bins.json") as f:
            f_data = f.read()
        payload = json.loads(f_data)
        payload["metadata"]["root"]["signed"]["vendor-url"] = "http://url.com"

        response = test_client.post(BOOTSTRAP_URL, json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert (
            "unrecognized_field must use format x-<vendor>-<name>"
            in response.text
        )

    def test_post_bootstrap_custom_timeout(
        self, test_client, monkeypatch, fake_datetime
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="finished", task_id="task_id"
            )
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
        monkeypatch.setattr(f"{MOCK_PATH}.pre_lock_bootstrap", lambda *a: None)
        mocked__check_bootstrap_status = pretend.call_recorder(lambda *a: None)
        monkeypatch.setattr(
            f"{MOCK_PATH}._check_bootstrap_status",
            mocked__check_bootstrap_status,
        )

        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)

        with open("tests/data_examples/bootstrap/payload_bins.json") as f:
            f_data = f.read()
        payload = json.loads(f_data)
        payload["timeout"] = 600

        response = test_client.post(BOOTSTRAP_URL, json=payload)

        assert fake_datetime.now.calls == [pretend.call(timezone.utc)]
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert response.json() == {
            "message": "Bootstrap accepted.",
            "data": {"task_id": "123", "last_update": "2019-06-16T09:05:01Z"},
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked__check_bootstrap_status.calls == [
            pretend.call(task_id="123", timeout=600)
        ]

    def test_post_bootstrap_already_bootstrap(self, test_client, monkeypatch):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=True, state="finished", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        with open("tests/data_examples/bootstrap/payload_bins.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(BOOTSTRAP_URL, json=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert response.json() == {
            "detail": {
                "error": "System already has a Metadata. State: finished"
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_bootstrap_already_bootstrap_in_pre(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="pre", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        with open("tests/data_examples/bootstrap/payload_bins.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(BOOTSTRAP_URL, json=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert response.json() == {
            "detail": {"error": "System already has a Metadata. State: pre"}
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_bootstrap_already_bootstrap_in_signing(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="signing", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        with open("tests/data_examples/bootstrap/payload_bins.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        response = test_client.post(BOOTSTRAP_URL, json=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert response.json() == {
            "detail": {
                "error": "System already has a Metadata. State: signing"
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_post_bootstrap_empty_payload(self, test_client):
        response = test_client.post(BOOTSTRAP_URL, json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        assert response.json() == {
            "detail": [
                {
                    "input": {},
                    "loc": ["body", "settings"],
                    "msg": "Field required",
                    "type": "missing",
                    "url": "https://errors.pydantic.dev/2.6/v/missing",
                },
                {
                    "input": {},
                    "loc": ["body", "metadata"],
                    "msg": "Field required",
                    "type": "missing",
                    "url": "https://errors.pydantic.dev/2.6/v/missing",
                },
            ]
        }

    def test_post_payload_no_bins_or_delegated_targets(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="finished", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        with open("tests/data_examples/bootstrap/payload_bins.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        del payload["settings"]["roles"]["bins"]
        response = test_client.post(BOOTSTRAP_URL, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        err_msg = "Exactly one of 'bins' and 'delegated_roles' must be set"
        assert err_msg in response.text

    @pytest.mark.parametrize("name", ["bad*", "|bad", ".bad", "/", "\\"])
    def test_post_payload_bad_delegated_role_names(
        self, test_client, monkeypatch, name
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="finished", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        path = "tests/data_examples/bootstrap/payload_custom_targets.json"
        with open(path) as f:
            f_data = f.read()

        payload = json.loads(f_data)
        payload["settings"]["roles"]["delegated_roles"] = {
            name: {"expiration": 30, "path_prefixes": ["project/f"]},
        }
        response = test_client.post(BOOTSTRAP_URL, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        err_msg_1 = "Delegated custom target name"
        err_msg_2 = "not allowed"
        err_msg_3 = " Only a-z, A-Z, 0-9, - and _ characters can be used"
        assert err_msg_1 in response.text
        assert err_msg_2 in response.text
        assert err_msg_3 in response.text

    def test_post_payload_delegated_role_with_empty_path_pattern(
        self, test_client, monkeypatch
    ):
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(
                bootstrap=False, state="finished", task_id="task_id"
            )
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        path = "tests/data_examples/bootstrap/payload_custom_targets.json"
        with open(path) as f:
            f_data = f.read()

        payload = json.loads(f_data)
        payload["settings"]["roles"]["delegated_roles"]["foo"] = {
            "expiration": 30,
            "path_patterns": [""],
        }
        response = test_client.post(BOOTSTRAP_URL, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.url == f"{test_client.base_url}{BOOTSTRAP_URL}"
        err_msg = "No empty strings are allowed as path patterns"
        assert err_msg in response.text
