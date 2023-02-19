from abc import ABC
from dataclasses import dataclass
from typing import Optional

from repository_service_tuf_api.rstuf_auth.models import Scope


@dataclass
class ScopeDTO:
    id: int
    name: str
    description: Optional[str] = None

    @classmethod
    def from_db(cls, scope: Scope) -> 'ScopeDTO':
        return ScopeDTO(
            id=scope.id,
            name=scope.name,
            description=scope.description
        )


class ScopeRepository(ABC):
    """

    """
    def create(self, name: str, description: Optional[str] = None) -> ScopeDTO:
        pass

    def get_all(self) -> list[ScopeDTO]:
        pass

    def get_by_id(self, id_: int) -> Optional[ScopeDTO]:
        pass

    def get_by_name(self, name: str) -> Optional[ScopeDTO]:
        pass
