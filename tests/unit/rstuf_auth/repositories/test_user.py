import pytest

from repository_service_tuf_api.rstuf_auth import exceptions
from repository_service_tuf_api.rstuf_auth.ports.user import UserDTO
from repository_service_tuf_api.rstuf_auth.repositories.scope import (
    ScopeSQLRepository,
)
from repository_service_tuf_api.rstuf_auth.repositories.user import (
    UserScopeSQLRepository,
    UserSQLRepository,
)


class TestUserSQLRepository:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.user_repo = UserSQLRepository(db_session)
        self.user = self.user_repo.create(username="test", password="test")

    def test_create(self):
        assert isinstance(self.user, UserDTO)
        assert self.user.id == 1
        assert self.user.username == "test"

    def test_create_existing_user(self):
        with pytest.raises(exceptions.UserAlreadyExists):
            self.user_repo.create(username="test", password="test")

    def test_get_by_id(self):
        get_user = self.user_repo.get_by_id(self.user.id)

        assert get_user == self.user

    def test_get_by_unknown_id(self):
        with pytest.raises(exceptions.UserNotFound):
            assert self.user_repo.get_by_id(999)

    def test_get_by_username(self):
        get_user = self.user_repo.get_by_username(self.user.username)

        assert get_user == self.user

    def test_get_by_unknown_username(self):
        with pytest.raises(exceptions.UserNotFound):
            assert self.user_repo.get_by_username("unknown_username")


class TestUserScopeSQLRepository:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.user_repo = UserSQLRepository(db_session)
        self.scope_repo = ScopeSQLRepository(db_session)
        self.user_scope_repo = UserScopeSQLRepository(db_session)

        self.user = self.user_repo.create(username="test", password="test")
        self.write_scope = self.scope_repo.create(
            name="write:test", description="write test"
        )
        self.read_scope = self.scope_repo.create(
            name="read:test", description="read test"
        )

    def test_get_scope_ids_of_user(self):
        self.user_scope_repo.add_scopes_to_user(
            self.user.id, [self.write_scope.id]
        )

        scopes_ids = self.user_scope_repo.get_scope_ids_of_user(self.user.id)

        assert scopes_ids == [self.write_scope.id]

    def test_get_scope_names_of_user(self):
        self.user_scope_repo.add_scopes_to_user(
            self.user.id, [self.write_scope.id]
        )

        scopes_names = self.user_scope_repo.get_scope_names_of_user(
            self.user.id
        )

        assert scopes_names == [self.write_scope.name]

        self.user_scope_repo.add_scopes_to_user(
            self.user.id, [self.read_scope.id]
        )

        scopes_names = self.user_scope_repo.get_scope_names_of_user(
            self.user.id
        )

        assert scopes_names == [self.write_scope.name, self.read_scope.name]
