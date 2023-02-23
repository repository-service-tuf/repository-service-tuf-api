from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import bcrypt

from repository_service_tuf_api.rstuf_auth.models import User


@dataclass
class UserDTO:
    id: int
    username: str
    password: bytes
    created_at: datetime

    @classmethod
    def from_db(cls, user: User) -> 'UserDTO':
        return UserDTO(
            id=user.id,
            username=user.username,
            password=user.password,
            created_at=user.created_at
        )


class UserRepository(ABC):
    """

    """
    @staticmethod
    def hash_password(password: str) -> bytes:
        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        )

        return hashed_password

    @staticmethod
    def verify_password(password: str, hashed_password: bytes) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password)

    @abstractmethod
    def create(
        self, username: str, password: str
    ) -> UserDTO:
        pass

    def get_by_id(self, user_id: int) -> Optional[UserDTO]:
        pass

    def get_by_username(self, username: str) -> Optional[UserDTO]:
        pass


class UserScopeRepository(ABC):

    def add_scopes_to_user(self, user_id: int, scopes: list[int]) -> None:
        pass

    def get_scope_ids_of_user(self, user_id: int) -> list[int]:
        pass

    def get_scope_names_of_user(self, user_id) -> list[str]:
        pass
