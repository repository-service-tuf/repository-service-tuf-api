from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from repository_service_tuf_api.rstuf_auth.models import Scope


@dataclass
class ScopeDTO:
    id: int
    name: str
    description: Optional[str] = None

    @classmethod
    def from_db(cls, scope: Scope) -> "ScopeDTO":
        return ScopeDTO(
            id=scope.id, name=scope.name, description=scope.description
        )


class ScopeRepository(ABC):
    """Abstract Class for the Scope Repository"""

    @abstractmethod
    def create(self, name: str, description: Optional[str] = None) -> ScopeDTO:
        """
        Create new scope

        :param name: the scope name
        :param description: the scope description

        :returns: A Scope Data Transfer Object
        """

    @abstractmethod
    def get_all(self) -> list[ScopeDTO]:
        """
        Get all available scopes

        :returns: A list of Scope Data Transfer Objects
        """

    def get_all_names(self) -> list[str]:
        """
        Get the names of all available scopes

        :returns: A list of names
        """

    @abstractmethod
    def get_by_id(self, id_: int) -> Optional[ScopeDTO]:
        """
        Get a scope by id

        :returns: A Scope Data Transfer Object
        """

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[ScopeDTO]:
        """
        Get a scope by name

        :returns: A Scope Data Transfer Object
        """
