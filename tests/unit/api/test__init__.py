# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from repository_service_tuf_api import api


class TestApiWithoutClient:
    def test_get_auth_is_true(self, caplog):
        caplog.set_level(api.logging.INFO)

        api.is_auth_enabled = True

        result = api.get_auth()

        assert result.__name__ == "validate_token"
        assert isinstance(result, api.Callable)
        assert caplog.record_tuples == [
            ("root", 20, "RSTUF builtin auth is enabled")
        ]

    def test_get_auth_is_false(self, caplog):
        caplog.set_level(api.logging.INFO)
        api.is_auth_enabled = False

        result = api.get_auth()

        assert result.__name__ == "<lambda>"
        assert result() is None
        assert isinstance(result, api.Callable)
        assert caplog.record_tuples == [
            ("root", 20, "RSTUF builtin auth is disabled")
        ]
