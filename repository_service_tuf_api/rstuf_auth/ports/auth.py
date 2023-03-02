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
    def create_user(self, username: str, password: str) -> UserDTO:
        pass

    def issue_token(
        self,
        username: str,
        scopes: list[str],
        expires_delta: Optional[int] = 1,
        password: Optional[str] = None,
    ) -> TokenDTO:
        pass

    def validate_token(
        self, token: str, required_scopes: Optional[list[str]] = None
    ) -> TokenDTO:
        pass
