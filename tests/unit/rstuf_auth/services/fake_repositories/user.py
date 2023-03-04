from collections import defaultdict
from datetime import datetime

from repository_service_tuf_api.rstuf_auth import exceptions
from repository_service_tuf_api.rstuf_auth.ports.scope import ScopeRepository
from repository_service_tuf_api.rstuf_auth.ports.user import (
    UserDTO,
    UserRepository,
    UserScopeRepository,
)


class FakeUserRepository(UserRepository):
    def __init__(self):
        self.users_id = {}
        self.users_by_username = {}
        self.index = 0

    def create(self, username: str, password: str) -> UserDTO:
        self.index += 1
        user = UserDTO(
            id=self.index,
            username=username,
            password=self.hash_password(password),
            created_at=datetime.utcnow(),
        )

        self.users_id[self.index] = user
        self.users_by_username[username] = user

        return user

    def get_by_id(self, user_id: int) -> UserDTO:
        try:
            user = self.users_id[user_id]
        except KeyError:
            raise exceptions.UserNotFound

        return user

    def get_by_username(self, username: str) -> UserDTO:
        try:
            user = self.users_by_username[username]
        except KeyError:
            raise exceptions.UserNotFound

        return user


class FakeUserScopeRepository(UserScopeRepository):
    def __init__(self, scope_repo: ScopeRepository):
        self.scopes_per_user = defaultdict(list)
        self.scope_repo = scope_repo

    def add_scopes_to_user(self, user_id: int, scopes: list[int]) -> None:
        self.scopes_per_user[user_id].extend(scopes)

    def get_scope_ids_of_user(self, user_id: int) -> list[int]:
        scopes = self.scopes_per_user.get(user_id)

        if scopes is None:
            return []

        return scopes

    def get_scope_names_of_user(self, user_id) -> list[str]:
        scopes = self.get_scope_ids_of_user(user_id)

        return [self.scope_repo.get_by_id(scope).name for scope in scopes]
