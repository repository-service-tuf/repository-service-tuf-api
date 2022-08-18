import datetime
from dataclasses import dataclass
from typing import List

import pretend
from fastapi import status


class TestPostTargets:
    def test_post(self, monkeypatch, test_client):
        mocked_datetime = pretend.stub(
            utcnow=pretend.call_recorder(
                lambda: datetime.datetime(2019, 6, 16, 7, 5, 00, 355186)
            )
        )
        monkeypatch.setattr("kaprien_api.token.datetime", mocked_datetime)
        url = "/api/v1/token/?expires=2"
        token_data = {
            "username": "admin",
            "password": "secret",
            "scope": "write:targets",
        }
        response = test_client.post(url, data=token_data)
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()

    def test_post_without_expires(self, monkeypatch, test_client):
        mocked_datetime = pretend.stub(
            utcnow=pretend.call_recorder(
                lambda: datetime.datetime(2019, 6, 16, 9, 5, 00, 355186)
            )
        )
        monkeypatch.setattr("kaprien_api.token.datetime", mocked_datetime)
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
                scopes=[Scope("read:targets")],
            )
        )
        monkeypatch.setattr(
            "kaprien_api.api.token.get_user_by_username", fake_user_db
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
