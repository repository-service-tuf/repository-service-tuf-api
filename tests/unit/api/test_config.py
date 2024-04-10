# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
from datetime import timezone

import pretend
from fastapi import status

URL = "/api/v1/config"
MOCK_PATH = "repository_service_tuf_api.config"


class TestPutSettings:
    def test_put_settings(self, test_client, monkeypatch, fake_datetime):
        with open("tests/data_examples/config/update_settings.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        mocked_get_task_id = pretend.call_recorder(lambda: "task-id")
        monkeypatch.setattr(f"{MOCK_PATH}.get_task_id", mocked_get_task_id)
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda **kw: None)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata", mocked_repository_metadata
        )
        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)
        response = test_client.put(URL, json=payload)
        assert fake_datetime.now.calls == [pretend.call(timezone.utc)]
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "data": {
                "task_id": "task-id",
                "last_update": "2019-06-16T09:05:01Z",
            },
            "message": "Settings successfully submitted.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_get_task_id.calls == [pretend.call()]
        assert mocked_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={"action": "update_settings", "payload": payload},
                task_id="task-id",
                queue="metadata_repository",
                acks_late=True,
            )
        ]

    def test_put_settings_with_custom_targets(
        self, test_client, monkeypatch, fake_datetime
    ):
        path = "tests/data_examples/config/update_settings_custom_targets.json"
        with open(path) as f:
            f_data = f.read()

        payload = json.loads(f_data)

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        mocked_get_task_id = pretend.call_recorder(lambda: "task-id")
        monkeypatch.setattr(f"{MOCK_PATH}.get_task_id", mocked_get_task_id)
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda **kw: None)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata", mocked_repository_metadata
        )

        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)
        response = test_client.put(URL, json=payload)
        assert fake_datetime.now.calls == [pretend.call(timezone.utc)]
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {
            "data": {
                "task_id": "task-id",
                "last_update": "2019-06-16T09:05:01Z",
            },
            "message": "Settings successfully submitted.",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert mocked_get_task_id.calls == [pretend.call()]
        assert mocked_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={"action": "update_settings", "payload": payload},
                task_id="task-id",
                queue="metadata_repository",
                acks_late=True,
            )
        ]

    def test_put_settings_without_bootstrap(self, test_client, monkeypatch):
        with open("tests/data_examples/config/update_settings.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state=None)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        response = test_client.put(URL, json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": {
                "message": "No Repository Settings/Config found.",
                "error": "It requires bootstrap. State: None",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_put_settings_intermediate_state(self, test_client, monkeypatch):
        with open("tests/data_examples/config/update_settings.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state="signing")
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        response = test_client.put(URL, json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": {
                "message": "No Repository Settings/Config found.",
                "error": "It requires bootstrap. State: signing",
            }
        }

        assert mocked_bootstrap_state.calls == [pretend.call()]


class TestGetSettings:
    def test_get_settings(self, test_client, monkeypatch):
        url = "/api/v1/config"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True)
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )
        fake_settings = pretend.stub(
            fresh=pretend.call_recorder(lambda: None),
            to_dict=pretend.call_recorder(
                lambda: {"k": "v", "j": ["v1", "v2"], "l": "none"}
            ),
        )
        monkeypatch.setattr(f"{MOCK_PATH}.settings_repository", fake_settings)

        test_response = test_client.get(url)
        assert test_response.status_code == status.HTTP_200_OK
        assert test_response.json() == {
            "data": {"k": "v", "j": ["v1", "v2"]},
            "message": "Current Settings",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert fake_settings.fresh.calls == [pretend.call()]
        assert fake_settings.to_dict.calls == [pretend.call()]

    def test_get_settings_without_bootstrap(self, test_client, monkeypatch):
        url = "/api/v1/config"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state="None")
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state", mocked_bootstrap_state
        )

        test_response = test_client.get(url)
        assert test_response.status_code == status.HTTP_404_NOT_FOUND
        assert test_response.json() == {
            "detail": {
                "message": "No Repository Settings/Config found.",
                "error": "It requires bootstrap. State: None",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
