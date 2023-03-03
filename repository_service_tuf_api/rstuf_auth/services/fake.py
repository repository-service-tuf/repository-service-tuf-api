# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
#
# ONLY FOR TESTING

import uuid
from calendar import timegm
from datetime import datetime, timedelta
from typing import Optional

from repository_service_tuf_api.rstuf_auth import exceptions
from repository_service_tuf_api.rstuf_auth.ports.auth import (
    AuthenticationService,
    TokenDTO,
)
from repository_service_tuf_api.rstuf_auth.ports.user import UserDTO


class FakeAuthenticationService(AuthenticationService):
    def __init__(self, scopes):
        self.available_scopes = scopes

        self.users: dict[str, UserDTO] = {}
        self.user_index = 0

        self.user_scopes: dict[int, set[str]] = {}

        self.tokens: dict[str, TokenDTO] = {}

    def create_user(
        self, username: str, password: str, scopes: Optional[list[str]] = None
    ) -> UserDTO:
        self.user_index += 1
        user = UserDTO(
            id=self.user_index,
            created_at=datetime.utcnow(),
            password=str.encode(password),
            username=username,
        )

        self.users[username] = user
        self.add_scopes_to_user(user.id, scopes or [])

        return user

    def add_scopes_to_user(self, user_id: int, scopes: list[str]) -> None:
        self.user_scopes[user_id] = set(scopes) if scopes is not None else []

    def issue_token(
        self,
        username: str,
        scopes: list[str],
        expires_delta: Optional[int] = 1,
        password: Optional[str] = None,
    ) -> TokenDTO:
        try:
            user = self.users[username]
        except KeyError:
            raise exceptions.UserNotFound

        if password and str.encode(password) != user.password:
            raise exceptions.InvalidPassword

        for scope in scopes:
            if scope not in self.user_scopes[user.id]:
                raise exceptions.ScopeNotFoundInUserScopes(scope=scope)

        expires = datetime.utcnow() + timedelta(hours=expires_delta)

        token = TokenDTO(
            username=username,
            access_token=uuid.uuid4().hex,
            expires_at=timegm(expires.utctimetuple()),
            scopes=scopes,
            sub=f"user_{user.id}_{uuid.uuid4().hex}",
        )

        self.tokens[token.access_token] = token

        return token

    def validate_token(
        self, token: str, required_scopes: Optional[list[str]] = None
    ) -> TokenDTO:
        try:
            user_token = self.tokens[token]
        except KeyError:
            raise exceptions.InvalidTokenFormat

        try:
            self.users[user_token.username]
        except KeyError:
            raise exceptions.UserNotFound

        if any(
            required_scope
            for required_scope in required_scopes or []
            if required_scope not in user_token.scopes
        ):
            raise exceptions.ScopeNotProvided

        return user_token
