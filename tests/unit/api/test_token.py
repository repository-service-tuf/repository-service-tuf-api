# SPDX-FileCopyrightText: 2022 VMware Inc
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import datetime
from typing import List

import pretend
from fastapi import status


class TestGetToken:
    def test_get(self, test_client, token_headers):
        token_url = "/api/v1/token/?expires=1"
        token_payload = {
            "username": "admin",
            "password": "secret",
            "scope": "write:targets",
        }
        response = test_client.post(token_url, data=token_payload)
        test_token = response.json().get("access_token")

        url = f"/api/v1/token/?token={test_token}"
        response = test_client.get(url, headers=token_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["scopes"] == ["write:targets"]
        assert response.json()["data"]["expired"] is False

    def test_get_fake_token(self, test_client, token_headers):
        url = "/api/v1/token/?token=fake_token"
        response = test_client.get(url, headers=token_headers)

        assert response.status_code == status.HTTP_200_OK

    def test_get_expired_token(self, test_client, monkeypatch, token_headers):
        token_url = "/api/v1/token/?expires=1"
        token_payload = {
            "username": "admin",
            "password": "secret",
            "scope": "write:targets",
        }
        response = test_client.post(token_url, data=token_payload)
        test_token = response.json().get("access_token")
        mocked_datetime = pretend.stub(
            utcnow=datetime.utcnow(),
            now=pretend.call_recorder(lambda: datetime.now()),
            fromtimestamp=pretend.call_recorder(
                lambda *a: datetime(2019, 6, 16, 7, 5, 00, 355186)
            ),
        )

        monkeypatch.setattr(
            "repository_service_tuf_api.token.datetime",
            mocked_datetime,
        )
        url = f"/api/v1/token/?token={test_token}"
        response = test_client.get(url, headers=token_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["scopes"] == ["write:targets"]
        assert response.json()["data"]["expired"] is True


class TestPostToken:
    def test_post(self, monkeypatch, test_client):
        mocked_datetime = pretend.stub(
            utcnow=pretend.call_recorder(
                lambda: datetime(2019, 6, 16, 7, 5, 00, 355186)
            )
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.token.datetime", mocked_datetime
        )
        url = "/api/v1/token/?expires=2"
        token_data = {
            "username": "admin",
            "password": "secret",
            "scope": (
                "read:bootstrap read:settings read:tasks read:token "
                "write:targets delete:targets"
            ),
        }
        response = test_client.post(url, data=token_data)
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()

    def test_post_without_expires(self, monkeypatch, test_client):
        mocked_datetime = pretend.stub(
            utcnow=pretend.call_recorder(
                lambda: datetime(2019, 6, 16, 9, 5, 00, 355186)
            )
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.token.datetime", mocked_datetime
        )
        url = "/api/v1/token/"
        token_data = {
            "username": "admin",
            "password": "secret",
            "scope": "write:targets",
        }
        response = test_client.post(url, data=token_data)
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()

    def test_post_unauthorized_wrong_user(self, test_client):
        token_url = "/api/v1/token/?expires=1"
        token_payload = {
            "username": "root",
            "password": "secret",
            "scope": "write:targets",
        }
        token = test_client.post(token_url, data=token_payload)

        assert token.status_code == status.HTTP_401_UNAUTHORIZED
        assert token.json() == {"detail": "Unauthorized"}

    def test_post_unauthorized_wrong_password(self, test_client):
        token_url = "/api/v1/token/?expires=1"
        token_payload = {
            "username": "admin",
            "password": "secrets",
            "scope": "write:targets",
        }
        token = test_client.post(token_url, data=token_payload)

        assert token.status_code == status.HTTP_401_UNAUTHORIZED
        assert token.json() == {"detail": "Unauthorized"}

    def test_post_forbidden_user_forbidden_to_request_scope(
        self, monkeypatch, test_client
    ):
        @dataclass
        class Scope:
            name: str

        @dataclass
        class User:
            id: int
            username: str
            password: str
            scopes: List[Scope]

        fake_user_db = pretend.call_recorder(
            lambda *a: User(
                id=1213,
                username="read_user",
                password="test",
                scopes=[Scope("read:settings")],
            )
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.token.get_user_by_username",
            fake_user_db,
        )

        mocked_bcrypt = pretend.stub(
            checkpw=pretend.call_recorder(lambda *a: True)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.token.bcrypt", mocked_bcrypt
        )

        token_url = "/api/v1/token/?expires=1"
        token_payload = {
            "username": "read_user",
            "password": "test",
            "scope": "write:targets",
        }
        token = test_client.post(token_url, data=token_payload)

        assert token.status_code == status.HTTP_403_FORBIDDEN
        assert token.json() == {
            "detail": {"error": "scope 'write:targets' forbidden"}
        }
        assert mocked_bcrypt.checkpw.calls == [pretend.call(b"test", "test")]

    def test_post_with_empty_scope(self, test_client):
        url = "/api/v1/token/"
        token_data = {
            "username": "admin",
            "password": "secret",
            "scope": "''",
        }
        response = test_client.post(url, data=token_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"]["error"] == "scope '''' forbidden"

    def test_post_with_missing_scope(self, test_client):
        url = "/api/v1/token/"
        token_data = {
            "username": "admin",
            "password": "secret",
            "scope": None,
        }
        response = test_client.post(url, data=token_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_post_with_expires_0(self, test_client):
        url = "/api/v1/token/"
        token_data = {
            "username": "admin",
            "password": "secret",
            "scope": ["write:targets"],
            "expires": 0,
        }
        response = test_client.post(url, data=token_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            response.json()["detail"][0]["msg"]
            == "ensure this value is greater than or equal to 1"
        )

    def test_post_with_expires_negative(self, test_client):
        url = "/api/v1/token/"
        token_data = {
            "username": "admin",
            "password": "secret",
            "scope": ["write:targets"],
            "expires": -25,
        }
        response = test_client.post(url, data=token_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            response.json()["detail"][0]["msg"]
            == "ensure this value is greater than or equal to 1"
        )

    def test_post_new(self, test_client, token_headers):
        url = "/api/v1/token/new/"
        payload = {
            "scopes": [
                "read:bootstrap",
                "read:settings",
                "read:tasks",
                "read:token",
                "write:targets",
                "delete:targets",
            ],
            "expires": 1,
        }

        response = test_client.post(url, headers=token_headers, json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()

    def test_post_new_with_empty_scope(self, test_client, token_headers):
        url = "/api/v1/token/new/"
        payload = {
            "scopes": [],
            "expires": 1,
        }

        response = test_client.post(url, headers=token_headers, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            response.json()["detail"][0]["msg"]
            == "ensure this value has at least 1 items"
        )

    def test_post_new_with_scopes_with_empty_string(
        self, test_client, token_headers
    ):
        url = "/api/v1/token/new/"
        payload = {
            "scopes": [""],
            "expires": 1,
        }

        response = test_client.post(url, headers=token_headers, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "unexpected value" in response.json()["detail"][0]["msg"]

    def test_post_new_with_scopes_with_invalid_scope(
        self, test_client, token_headers
    ):
        url = "/api/v1/token/new/"
        payload = {
            "scopes": ["invalid"],
            "expires": 1,
        }

        response = test_client.post(url, headers=token_headers, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "unexpected value" in response.json()["detail"][0]["msg"]

    def test_post_new_with_expires_0(self, test_client, token_headers):
        url = "/api/v1/token/new/"
        payload = {
            "scopes": ["write:targets"],
            "expires": 0,
        }
        response = test_client.post(url, headers=token_headers, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            response.json()["detail"][0]["msg"]
            == "ensure this value is greater than or equal to 1"
        )

    def test_post_new_with_expires_negative(self, test_client, token_headers):
        url = "/api/v1/token/new/"
        payload = {
            "scopes": ["write:targets"],
            "expires": -31,
        }
        response = test_client.post(url, headers=token_headers, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            response.json()["detail"][0]["msg"]
            == "ensure this value is greater than or equal to 1"
        )

    def test_post_new_with_expires_missing(self, test_client, token_headers):
        url = "/api/v1/token/new/"
        payload = {
            "scopes": ["write:targets"],
        }
        response = test_client.post(url, headers=token_headers, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"][0]["msg"] == "field required"

    def test_post_new_with_expires_none(self, test_client, token_headers):
        url = "/api/v1/token/new/"
        payload = {"scopes": ["write:targets"], "expires": None}
        response = test_client.post(url, headers=token_headers, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            response.json()["detail"][0]["msg"]
            == "none is not an allowed value"
        )
