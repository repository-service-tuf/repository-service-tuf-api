# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json

import pretend
from fastapi import status

URL = "/api/v1/config"


class TestPutSettings:
    def test_put_settings(self, test_client, token_headers, monkeypatch):
        with open("tests/data_examples/config/update_settings.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.config.bootstrap_state",
            mocked_bootstrap_state,
        )
        mocked_get_task_id = pretend.call_recorder(lambda: "task-id")
        monkeypatch.setattr(
            "repository_service_tuf_api.config.get_task_id", mocked_get_task_id
        )
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda **kw: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.config.repository_metadata",
            mocked_repository_metadata,
        )
        response = test_client.put(URL, json=payload, headers=token_headers)
        assert response.status_code == status.HTTP_202_ACCEPTED
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

    def test_put_settings_without_bootstrap(
        self, test_client, token_headers, monkeypatch
    ):
        with open("tests/data_examples/config/update_settings.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state=None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.config.bootstrap_state",
            mocked_bootstrap_state,
        )
        response = test_client.put(URL, json=payload, headers=token_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": {
                "message": "No Repository Settings/Config found.",
                "error": "It requires bootstrap. State: None",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_put_settings_intermediate_state(
        self, test_client, token_headers, monkeypatch
    ):
        with open("tests/data_examples/config/update_settings.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state="signing")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.config.bootstrap_state",
            mocked_bootstrap_state,
        )
        response = test_client.put(URL, json=payload, headers=token_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            "detail": {
                "message": "No Repository Settings/Config found.",
                "error": "It requires bootstrap. State: signing",
            }
        }

        assert mocked_bootstrap_state.calls == [pretend.call()]


class TestGetSettings:
    def test_get_settings(self, test_client, token_headers, monkeypatch):
        url = "/api/v1/config"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=True)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.config.bootstrap_state",
            mocked_bootstrap_state,
        )
        fake_settings = pretend.stub(
            fresh=pretend.call_recorder(lambda: None),
            to_dict=pretend.call_recorder(
                lambda: {"k": "v", "j": ["v1", "v2"], "l": "none"}
            ),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.config.settings_repository",
            fake_settings,
        )

        test_response = test_client.get(url, headers=token_headers)
        assert test_response.status_code == status.HTTP_200_OK
        assert test_response.json() == {
            "data": {"k": "v", "j": ["v1", "v2"]},
            "message": "Current Settings",
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]
        assert fake_settings.fresh.calls == [pretend.call()]
        assert fake_settings.to_dict.calls == [pretend.call()]

    def test_get_settings_without_bootstrap(
        self, test_client, token_headers, monkeypatch
    ):
        url = "/api/v1/config"

        mocked_bootstrap_state = pretend.call_recorder(
            lambda *a: pretend.stub(bootstrap=False, state="None")
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.config.bootstrap_state",
            mocked_bootstrap_state,
        )

        test_response = test_client.get(url, headers=token_headers)
        assert test_response.status_code == status.HTTP_404_NOT_FOUND
        assert test_response.json() == {
            "detail": {
                "message": "No Repository Settings/Config found.",
                "error": "It requires bootstrap. State: None",
            }
        }
        assert mocked_bootstrap_state.calls == [pretend.call()]

    def test_get_settings_invalid_token(self, test_client, monkeypatch):
        url = "/api/v1/config"

        def fake_get(arg):
            if "_EXPIRATION" in arg:
                return 30
            else:
                return "fake_value"

        fake_backend = pretend.stub(
            name="FakeBackend",
            required=True,
        )
        fake_settings = pretend.stub(
            STORAGE_BACKEND=pretend.stub(
                __name__="fake_storage_backend",
                settings=pretend.call_recorder(lambda: [fake_backend]),
            ),
            KEYVAULT_BACKEND=pretend.stub(
                __name__="fake_keyvault_backend",
                settings=pretend.call_recorder(lambda: [fake_backend]),
            ),
            get=pretend.call_recorder(fake_get),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.config.settings_repository",
            fake_settings,
        )
        token_headers = {"Authorization": "Bearer h4ck3r"}

        test_response = test_client.get(url, headers=token_headers)
        assert test_response.status_code == status.HTTP_401_UNAUTHORIZED
        assert test_response.json() == {
            "detail": {"error": "Failed to validate token"}
        }
