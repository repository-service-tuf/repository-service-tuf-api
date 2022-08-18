import pretend
from fastapi import status


class TestGetSettings:
    def test_get_settings(self, test_client, token_headers, monkeypatch):
        url = "/api/v1/settings"

        mocked_check_metadata = pretend.call_recorder(lambda: True)
        monkeypatch.setattr(
            "kaprien_api.repository_settings.check_metadata",
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
            "kaprien_api.repository_settings.settings", fake_settings
        )

        test_response = test_client.get(url, headers=token_headers)
        assert test_response.status_code == status.HTTP_200_OK
        assert sorted(list(test_response.json()["data"].keys())) == [
            "keyvault_backend",
            "roles_expirations",
            "storage_backend",
        ]
        assert test_response.json()["message"] == "Current Settings"
        assert fake_settings.STORAGE_BACKEND.settings.calls == [pretend.call()]
        assert fake_settings.KEYVAULT_BACKEND.settings.calls == [
            pretend.call()
        ]
        assert fake_settings.get.calls == [
            pretend.call("FakeBackend"),
            pretend.call("FakeBackend"),
            pretend.call("root_EXPIRATION"),
            pretend.call("targets_EXPIRATION"),
            pretend.call("snapshot_EXPIRATION"),
            pretend.call("timestamp_EXPIRATION"),
            pretend.call("bin_EXPIRATION"),
            pretend.call("bins_EXPIRATION"),
        ]

    def test_get_settings_without_bootstrap(
        self, test_client, token_headers, monkeypatch
    ):
        url = "/api/v1/settings"

        mocked_check_metadata = pretend.call_recorder(lambda: False)
        monkeypatch.setattr(
            "kaprien_api.repository_settings.check_metadata",
            mocked_check_metadata,
        )

        test_response = test_client.get(url, headers=token_headers)
        assert test_response.status_code == status.HTTP_404_NOT_FOUND
        assert (
            test_response.json().get("detail").get("error")
            == "System has not a Repository Metadata"
        )

    def test_get_settings_invalid_token(self, test_client, monkeypatch):
        url = "/api/v1/settings"

        mocked_check_metadata = pretend.call_recorder(lambda: True)
        monkeypatch.setattr(
            "kaprien_api.repository_settings.check_metadata",
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
            "kaprien_api.repository_settings.settings", fake_settings
        )
        token_headers = {"Authorization": "Bearer h4ck3r"}

        test_response = test_client.get(url, headers=token_headers)
        assert test_response.status_code == status.HTTP_401_UNAUTHORIZED
        assert test_response.json() == {
            "detail": {"error": "Failed to validate token"}
        }
