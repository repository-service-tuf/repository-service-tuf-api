import logging
import os
from calendar import timegm
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Type
from uuid import uuid4

from jose import JWTError, jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from repository_service_tuf_api.rstuf_auth import exceptions
from repository_service_tuf_api.rstuf_auth.models import Base
from repository_service_tuf_api.rstuf_auth.ports.scope import ScopeRepository
from repository_service_tuf_api.rstuf_auth.ports.user import (
    UserDTO,
    UserRepository,
    UserScopeRepository,
)
from repository_service_tuf_api.rstuf_auth.repositories.scope import (
    ScopeSQLRepository,
)
from repository_service_tuf_api.rstuf_auth.repositories.user import (
    UserScopeSQLRepository,
    UserSQLRepository,
)

__all__ = ["CustomSQLAuthenticationService"]


@dataclass
class TokenDTO:
    access_token: str
    expires_at: int
    scopes: list[str]
    username: str
    sub: str


class UserDB:
    def __init__(self, settings, base_dir: str):
        self.db_url = settings.get(
            "DATABASE_URL",
            f"sqlite:///{os.path.join(base_dir, 'users.sqlite')}",
        )

        self.engine = create_engine(
            self.db_url, connect_args={"check_same_thread": False}
        )

        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        Base.metadata.create_all(bind=self.engine)

        self.session = SessionLocal()


def _admin_password_from_settings(secrets_settings) -> str:
    if secrets_settings.get("ADMIN_PASSWORD").startswith("/run/secrets/"):
        try:
            with open(secrets_settings.ADMIN_PASSWORD) as f:
                admin_password = f.read().rstrip("\n")
        except OSError as err:
            logging.error(str(err))
            raise exceptions.AdminPasswordNotFoundInSettings

    else:
        admin_password = secrets_settings.get("ADMIN_PASSWORD")

    return admin_password


def _secret_key_from_settings(secrets_settings) -> str:
    if secrets_settings.get("TOKEN_KEY").startswith("/run/secrets/"):
        try:
            with open(secrets_settings.TOKEN_KEY) as f:
                secret_key = f.read().rstrip("\n")
        except OSError as err:
            logging.error(str(err))
            raise exceptions.SecretKeyNotFoundInSettings

    else:
        secret_key = secrets_settings.get("TOKEN_KEY")

    return secret_key


class CustomAuthenticationService:
    """A Built-in Authentication Service Class"""

    def __init__(
        self,
        secrets_settings,
        scopes: dict[str, str],
        user_repo: UserRepository,
        scope_repo: ScopeRepository,
        user_scope_repo: UserScopeRepository,
    ):
        self._user_repo = user_repo
        self._scope_repo = scope_repo
        self._user_scope_repo = user_scope_repo

        for scope_name, scope_description in scopes.items():
            scope = self._scope_repo.get_by_name(name=scope_name)

            if not scope:
                self._scope_repo.create(
                    name=scope_name, description=scope_description
                )

        admin_password = _admin_password_from_settings(secrets_settings)
        self._initiate_admin(admin_password)

        self.secret_key = _secret_key_from_settings(secrets_settings)

    def create_user(self, username: str, password: str) -> UserDTO:
        user = self._user_repo.create(username=username, password=password)

        return user

    def _initiate_admin(self, password: str) -> None:
        user = self._user_repo.get_by_username(username="admin")

        if not user:
            user = self.create_user("admin", password)

        user_scope_ids = self._user_scope_repo.get_scope_ids_of_user(user.id)
        available_scopes = self._scope_repo.get_all()

        available_scope_ids = [scope.id for scope in available_scopes]
        user_missing_scopes = list(
            set(available_scope_ids) - set(user_scope_ids)
        )
        self._user_scope_repo.add_scopes_to_user(user.id, user_missing_scopes)

    def issue_token(
        self,
        username: str,
        scopes: list[str],
        expires_delta: Optional[int] = 1,
        password: Optional[str] = None,
    ) -> TokenDTO:
        db_user = self._user_repo.get_by_username(username)

        if not db_user:
            raise exceptions.UserNotFound

        if password:
            if not self._user_repo.verify_password(password, db_user.password):
                raise exceptions.InvalidPassword

        for scope in scopes:
            if scope not in self._user_scope_repo.get_scope_names_of_user(
                db_user.id
            ):
                raise exceptions.ScopeNotFoundInUserScopes(scope=scope)

        to_encode = {
            "sub": f"user_{db_user.id}_{uuid4().hex}",
            "username": db_user.username,
            "scopes": scopes,
        }

        expires = datetime.utcnow() + timedelta(hours=expires_delta)

        to_encode["exp"] = expires
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")

        return TokenDTO(
            username=username,
            access_token=encoded_jwt,
            expires_at=timegm(expires.utctimetuple()),
            scopes=scopes,
            sub=to_encode["sub"],
        )

    def _decode_token(self, token: str) -> dict:
        try:
            user_token = jwt.decode(
                token, self.secret_key, algorithms=["HS256"]
            )

        except JWTError:
            raise exceptions.InvalidTokenFormat

        return user_token

    def validate_token(
        self, token: str, required_scopes: Optional[list[str]] = None
    ) -> TokenDTO:
        user_token = self._decode_token(token)

        # TODO: Change username to sub
        db_user = self._user_repo.get_by_username(user_token["username"])

        if not db_user:
            raise exceptions.UserNotFound

        if any(
            required_scope
            for required_scope in required_scopes or []
            if required_scope not in user_token.get("scopes", [])
        ):
            raise exceptions.ScopeNotProvided

        return TokenDTO(
            access_token=token,
            username=user_token["username"],
            sub=user_token["sub"],
            scopes=[scope for scope in user_token["scopes"]],
            expires_at=user_token["exp"],
        )


class CustomSQLAuthenticationService(CustomAuthenticationService):
    """A Built-in Authentication Service Class with access to an SQL db"""

    def __init__(
        self,
        settings,
        secrets_settings,
        scopes: dict[str, str],
        base_dir: str,
        user_db: Type[UserDB] = UserDB,
        user_repo: Optional[UserRepository] = None,
        scope_repo: Optional[ScopeRepository] = None,
        user_scope_repo: Optional[UserScopeRepository] = None,
    ):
        self.user_db = user_db(settings, base_dir)
        self.session = self.user_db.session

        user_repo = user_repo or UserSQLRepository(self.session)
        scope_repo = scope_repo or ScopeSQLRepository(self.session)
        user_scope_repo = user_scope_repo or UserScopeSQLRepository(
            self.session
        )

        super().__init__(
            secrets_settings=secrets_settings,
            scopes=scopes,
            user_repo=user_repo,
            scope_repo=scope_repo,
            user_scope_repo=user_scope_repo,
        )
