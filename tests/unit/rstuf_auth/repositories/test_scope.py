import pytest

from repository_service_tuf_api.rstuf_auth import exceptions
from repository_service_tuf_api.rstuf_auth.ports.scope import ScopeDTO
from repository_service_tuf_api.rstuf_auth.repositories.scope import (
    ScopeSQLRepository,
)


class TestScopeSQLRepository:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.scope_repo = ScopeSQLRepository(db_session)

    def test_create(self):
        write_scope = self.scope_repo.create(
            name="write:test", description="write test"
        )

        assert isinstance(write_scope, ScopeDTO)
        assert write_scope.id == 1
        assert write_scope.name == "write:test"
        assert write_scope.description == "write test"

    def test_create_existing_scope(self):
        self.scope_repo.create(name="write:test", description="write test")

        with pytest.raises(exceptions.ScopeAlreadyExists):
            self.scope_repo.create(name="write:test", description="write test")

    def test_get_all(self):
        ws = self.scope_repo.create(name="write:test", description="write")
        rs = self.scope_repo.create(name="read:test", description="read")

        assert [ws, rs] == self.scope_repo.get_all()

    def test_get_by_id(self):
        ws = self.scope_repo.create(name="write:test", description="write")

        assert ws == self.scope_repo.get_by_id(ws.id)

    def test_get_by_unknown_id(self):
        assert self.scope_repo.get_by_id(999) is None

    def test_get_by_name(self):
        ws = self.scope_repo.create(name="write:test", description="write")

        assert ws == self.scope_repo.get_by_name(ws.name)

    def test_get_by_unknown_name(self):
        assert self.scope_repo.get_by_name("unknown_scope") is None

    def test_get_all_names(self):
        ws = self.scope_repo.create(name="write:test", description="write")
        rs = self.scope_repo.create(name="read:test", description="read")

        assert self.scope_repo.get_all_names() == [rs.name, ws.name]
