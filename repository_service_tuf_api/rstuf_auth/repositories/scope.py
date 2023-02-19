from typing import Optional

from sqlalchemy.orm import Session

from repository_service_tuf_api.rstuf_auth.models import Scope
from repository_service_tuf_api.rstuf_auth.ports.scope import (ScopeDTO,
                                                               ScopeRepository)


class ScopeSQLRepository(ScopeRepository):
    """

    """
    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str, description: Optional[str] = None) -> ScopeDTO:
        scope = Scope(name=name, description=description)
        self.session.add(scope)
        self.session.commit()

        return ScopeDTO.from_db(scope)

    def get_all(self) -> list[ScopeDTO]:
        db_scopes = self.session.query(Scope).all()

        return [ScopeDTO.from_db(db_scope) for db_scope in db_scopes]

    def get_by_id(self, id_: int) -> Optional[ScopeDTO]:
        db_scope = self.session.query(Scope).filter(
            Scope.id == id_
        ).first()

        if db_scope is None:
            return None

        return ScopeDTO.from_db(db_scope)

    def get_by_name(self, name: str) -> Optional[ScopeDTO]:
        db_scope = self.session.query(Scope).filter(
            Scope.name == name
        ).first()

        if db_scope is None:
            return None

        return ScopeDTO.from_db(db_scope)
