from abc import ABC
from dataclasses import dataclass
from typing import Optional

from repository_service_tuf_api.rstuf_auth.models import User
from repository_service_tuf_api.rstuf_auth.ports.scope import ScopeDTO


@dataclass
class UserDTO:
    id: int
    username: str
    password: bytes

    @classmethod
    def from_db(cls, user: User) -> 'UserDTO':
        return UserDTO(
            id=user.id,
            username=user.username,
            password=user.password,
        )


class UserRepository(ABC):
    """

    """
    def create(
        self, username: str, password: str
    ) -> UserDTO:
        pass

    def get_by_id(self, user_id: int) -> Optional[UserDTO]:
        pass

    def get_by_username(self, user_id: int) -> Optional[UserDTO]:
        pass


class UserScopeRepository(ABC):

    def add_scopes_to_user(
        self, user_id: int, scopes: list[ScopeDTO]
    ) -> None:
        pass

    def get_scope_ids_of_user(self, user_id: int) -> list[int]:
        pass

    def get_scope_names_of_user(self, user_id) -> list[str]:
        pass
