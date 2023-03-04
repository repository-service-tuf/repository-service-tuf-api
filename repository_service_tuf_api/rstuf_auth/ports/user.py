from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import bcrypt

from repository_service_tuf_api.rstuf_auth.models import User


@dataclass
class UserDTO:
    id: int
    username: str
    password: bytes
    created_at: datetime

    @classmethod
    def from_db(cls, user: User) -> "UserDTO":
        return UserDTO(
            id=user.id,
            username=user.username,
            password=user.password,
            created_at=user.created_at,
        )


class UserRepository(ABC):
    """Abstract class for the User Repository"""

    @staticmethod
    def hash_password(password: str) -> bytes:
        """
        Encrypt a password

        :param password: The password to encrypt

        :return: the encrypted password in bytes
        """
        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        )

        return hashed_password

    @staticmethod
    def verify_password(password: str, hashed_password: bytes) -> bool:
        """
        Verify whether a plain-text password is the same with a given
        encrypted password

        :param password: the plain-text password
        :param hashed_password: the enrypted password

        :returns: True when passwords match
        """
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password)

    @abstractmethod
    def create(self, username: str, password: str) -> UserDTO:
        """
        Add a new user to the datastore

        :param username: the username of the user
        :param password: the password of the user

        :returns: a User Data Object
        :raises: UserAlreadyExists
        """

    def get_by_id(self, user_id: int) -> UserDTO:
        """
        Search a user by ID

        :param user_id: the id of the user

        :returns: a User Data Object or None
        :raises: UserNotFound
        """

    def get_by_username(self, username: str) -> UserDTO:
        """
        Search a user by username

        :param username: the username of the user

        :returns: a User Data Object or None
        :raises: UserNotFound
        """


class UserScopeRepository(ABC):
    """Abstract Class for the UserScope Repository"""

    def add_scopes_to_user(self, user_id: int, scopes: list[int]) -> None:
        """
        Assign scopes to user

        :param user_id: the id of the user
        :param scopes: the list of the scopes to assign to the user
        """

    def get_scope_ids_of_user(self, user_id: int) -> list[int]:
        """
        Get all the scope ids of the user

        :param user_id: the id of the user

        :returns: a list of scope ids
        """

    def get_scope_names_of_user(self, user_id) -> list[str]:
        """
        Get all the scope names of the user

        :param user_id: the id of the user

        :returns: a list of scope names
        """
