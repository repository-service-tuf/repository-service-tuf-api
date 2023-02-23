from typing import Optional

from repository_service_tuf_api.rstuf_auth.ports.scope import (
    ScopeDTO, ScopeRepository)


class FakeScopeRepository(ScopeRepository):
    def __init__(self):
        self.scopes_by_id = {}
        self.scopes_by_name = {}
        self.index = 0

    def create(self, name: str, description: Optional[str] = None) -> ScopeDTO:
        self.index += 1

        scope = ScopeDTO(id=self.index, name=name, description=description)

        self.scopes_by_id[self.index] = scope
        self.scopes_by_name[name] = scope

        return scope

    def get_all(self) -> list[ScopeDTO]:
        return [scope for scope in self.scopes_by_id.values()]

    def get_by_id(self, id_: int) -> Optional[ScopeDTO]:
        return self.scopes_by_id.get(id_, None)

    def get_by_name(self, name: str) -> Optional[ScopeDTO]:
        return self.scopes_by_name.get(name, None)
