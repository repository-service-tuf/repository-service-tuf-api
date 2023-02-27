from typing import Optional

from sqlalchemy import exc as sql_exc
from sqlalchemy.orm import Session

from repository_service_tuf_api.rstuf_auth import exceptions
from repository_service_tuf_api.rstuf_auth.models import Scope, User, UserScope
from repository_service_tuf_api.rstuf_auth.ports.user import (
    UserDTO,
    UserRepository,
    UserScopeRepository,
)


class UserSQLRepository(UserRepository):
    """User Repository with access to an SQL database"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, username: str, password: str) -> UserDTO:
        db_user = User(
            username=username, password=self.hash_password(password)
        )

        try:
            self.session.add(db_user)
            self.session.commit()
        except sql_exc.IntegrityError:
            raise exceptions.UserAlreadyExists

        return UserDTO.from_db(db_user)

    def get_by_id(self, user_id: int) -> Optional[UserDTO]:
        user = self.session.query(User).filter(User.id == user_id).first()

        if user is None:
            return None

        return UserDTO.from_db(user)

    def get_by_username(self, username: str) -> Optional[UserDTO]:
        user = (
            self.session.query(User).filter(User.username == username).first()
        )

        if user is None:
            return None

        return UserDTO.from_db(user)


class UserScopeSQLRepository(UserScopeRepository):
    """UserScope Repository with access to an SQL database"""

    def __init__(self, session: Session):
        self.session = session

    def add_scopes_to_user(self, user_id: int, scopes: list[int]) -> None:
        for scope in scopes:
            db_obj = UserScope(user_id=user_id, scope_id=scope)
            self.session.add(db_obj)

        self.session.commit()

    def get_scope_ids_of_user(self, user_id: int) -> list[int]:
        user_scopes = (
            self.session.query(UserScope)
            .filter(UserScope.user_id == user_id)
            .all()
        )

        return [user_scope.scope_id for user_scope in user_scopes]

    def get_scope_names_of_user(self, user_id) -> list[str]:
        user_scopes = (
            self.session.query(Scope.name)
            .join(UserScope)
            .filter(UserScope.user_id == user_id)
            .all()
        )

        return [name for (name,) in user_scopes]
