# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import status


def test_root(test_client):
    response = test_client.get("/")

    assert response.url == test_client.base_url + "/"
    assert response.status_code == status.HTTP_200_OK
    assert "Repository Service for TUF API" in response.text


def test_default_notfound(test_client):
    response = test_client.get("/invalid_url")

    assert response.url == test_client.base_url + "/invalid_url"
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Not Found"}
