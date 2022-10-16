# SPDX-FileCopyrightText: 2022 VMware Inc
#
# SPDX-License-Identifier: MIT

import pretend
from fastapi import status


class TestGetSettings:
    def test_get_settings(self, test_client, token_headers, monkeypatch):
        url = "/api/v1/config"

        mocked_check_metadata = pretend.call_recorder(lambda: True)
        monkeypatch.setattr(
            "repository_service_tuf_api.config.is_bootstrap_done",
            mocked_check_metadata,
        )

        fake_settings = pretend.stub(
            to_dict=pretend.call_recorder(
                lambda: {"k": "v", "j": ["v1", "v2"]}
            )
        )
        monkeypatch.setattr("repository_service_tuf_api.config", fake_settings)

        test_response = test_client.get(url, headers=token_headers)
        assert test_response.status_code == status.HTTP_200_OK

    def test_get_settings_without_bootstrap(
        self, test_client, token_headers, monkeypatch
    ):
        url = "/api/v1/config"

        mocked_check_metadata = pretend.call_recorder(lambda: False)
        monkeypatch.setattr(
            "repository_service_tuf_api.config.is_bootstrap_done",
            mocked_check_metadata,
        )

        test_response = test_client.get(url, headers=token_headers)
        assert test_response.status_code == status.HTTP_404_NOT_FOUND
        assert (
            test_response.json().get("detail").get("error")
            == "System has not a Repository Metadata"
        )

    def test_get_settings_invalid_token(self, test_client, monkeypatch):
        url = "/api/v1/config"

        mocked_check_metadata = pretend.call_recorder(lambda: True)
        monkeypatch.setattr(
            "repository_service_tuf_api.config.is_bootstrap_done",
            mocked_check_metadata,
        )

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
