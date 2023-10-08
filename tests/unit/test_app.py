# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import status


class TestAPP:
    def test_root(self, test_client):
        response = test_client.get("/")

        assert response.url == f"{test_client.base_url}/"
        assert response.status_code == status.HTTP_200_OK
        assert "Repository Service for TUF API" in response.text

    def test_default_notfound(self, test_client):
        response = test_client.get("/invalid_url")

        assert response.url == f"{test_client.base_url}/invalid_url"
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Not Found"}

    def test_load_endpoints_disable_prefix_and_method(self, caplog):
        import app

        app.settings.DISABLE_ENDPOINTS = (
            "{'POST'}/api/v1/metadata/sign/:/api/v1/bootstrap/"
        )
        caplog.set_level(app.logging.INFO)
        app.load_endpoints()
        assert caplog.record_tuples == [
            ("root", 20, "Disabled endpoint /api/v1/bootstrap/"),
        ]

    def test_load_endpoints_disabling_priority_check(self, caplog):
        import app

        app.settings.DISABLE_ENDPOINTS = (
            "{'POST'}/api/v1/artifacts/publish/:/api/v1/artifacts/"
        )
        caplog.set_level(app.logging.INFO)
        app.load_endpoints()
        assert caplog.record_tuples == [
            (
                "root",
                20,
                "Disabled endpoint {'POST'}/api/v1/artifacts/publish/",
            ),
            ("root", 20, "Disabled endpoint /api/v1/artifacts/"),
        ]
