from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from repository_service_tuf_api.rstuf_auth.ports.user import UserDTO


@dataclass
class TokenDTO:
    access_token: str
    expires_at: int
    scopes: list[str]
    username: str
    sub: str


class AuthenticationService(ABC):
    """A Built-in Authentication Service Class"""

    @abstractmethod
    def create_user(
        self, username: str, password: str, scopes: Optional[list[str]] = None
    ) -> UserDTO:
        """
        Create a new user

        :param username: The username of the new user
        :param password: The plain-text password of the new user
        :param scopes: A list of scope names to assign to the user

        :returns: A User Data Transfer Object
        """

    def add_scopes_to_user(self, user_id: int, scopes: list[str]) -> None:
        """
        Add scopes to an existing user

        :param user_id: The id of the user
        :param scopes: The name of the scopes to add to a user
        """

    def issue_token(
        self,
        username: str,
        scopes: list[str],
        expires_delta: Optional[int] = 1,
        password: Optional[str] = None,
    ) -> TokenDTO:
        """
        Issue a new token for an existing user

        :param username: the username of the user
        :param scopes: the scopes to add to this token
        :param expires_delta: when the token expires in hours
        :param password: the password of the user

        :returns: A Token Transfer Data Object
        """

    def validate_token(
        self, token: str, required_scopes: Optional[list[str]] = None
    ) -> TokenDTO:
        """
        Validates a token:
         - is the token signed by this authority?
         - has the token expired?
         - does the user exists?
         - does the user has the required scopes?

        :param token: the encoded token
        :param required_scopes: the required scopes for this token, if any

        :returns: A Token Transfer Data Object
        """
