import os
from uuid import uuid4

import pytest
from dynaconf.utils import DynaconfDict

from repository_service_tuf_api.rstuf_auth.enums import ScopeName
from repository_service_tuf_api.rstuf_auth import exceptions
from repository_service_tuf_api.rstuf_auth.services.auth import \
    CustomAuthenticationService
from tests.unit.rstuf_auth.services.fake_repositories.scope import \
    FakeScopeRepository
from tests.unit.rstuf_auth.services.fake_repositories.user import \
    FakeUserRepository, FakeUserScopeRepository


class TestCustomAuthenticationService:
    mocked_secret_settings = DynaconfDict(
        {'ADMIN_PASSWORD': 'testSuperSecretPassword', 'TOKEN_KEY': uuid4().hex}
    )

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user_repo = FakeUserRepository()
        self.scope_repo = FakeScopeRepository()
        self.user_scope_repo = FakeUserScopeRepository(
            scope_repo=self.scope_repo
        )

        self.auth_service = CustomAuthenticationService(
            secrets_settings=self.mocked_secret_settings,
            user_repo=self.user_repo,
            scope_repo=self.scope_repo,
            user_scope_repo=self.user_scope_repo,
        )

    def test_initiate_admin(self):
        user = self.user_repo.get_by_username('admin')
        assert user is not None
        assert user.id == 1

        admin_scopes = self.user_scope_repo.get_scope_ids_of_user(user.id)
        available_scopes = [scope.id for scope in self.scope_repo.get_all()]
        assert admin_scopes == available_scopes != []
        assert self.user_repo.verify_password(
            self.mocked_secret_settings.get('ADMIN_PASSWORD'), user.password
        )

    @pytest.mark.parametrize(
        'password', [None, mocked_secret_settings.get('ADMIN_PASSWORD')]
    )
    def test_issue_token(self, password):
        token = self.auth_service.issue_token(
            username='admin',
            password=password,
            scopes=[ScopeName.write_bootstrap]
        )

        decoded_token = self.auth_service._decode_token(token.access_token)

        assert decoded_token['username'] == token.username == 'admin'
        assert decoded_token['sub'] == token.sub
        assert decoded_token['scopes'] == token.scopes == [
            ScopeName.write_bootstrap
        ]

    def test_issue_token_for_unknown_user(self):
        with pytest.raises(exceptions.UserNotFound):
            self.auth_service.issue_token(
                username='unknown_user', scopes=[ScopeName.write_bootstrap]
            )

    def test_issue_token_with_wrong_password(self):
        with pytest.raises(exceptions.InvalidPassword):
            self.auth_service.issue_token(
                username='admin',
                password='wrong_password',
                scopes=[ScopeName.write_bootstrap]
            )

    def test_issue_token_invalid_scopes(self):
        with pytest.raises(exceptions.ScopeNotFoundInUserScopes):
            self.auth_service.issue_token(
                username='admin', scopes=['invalid_scope']
            )

    def test_validate_token(self):
        token_dto = self.auth_service.issue_token(
            username='admin',
            password=self.mocked_secret_settings.get('ADMIN_PASSWORD'),
            scopes=[ScopeName.write_bootstrap]
        )

        validated_token_dto = self.auth_service.validate_token(
            token_dto.access_token
        )

        assert validated_token_dto == token_dto

    def test_validate_an_invalid_token(self):
        with pytest.raises(exceptions.InvalidTokenFormat):
            self.auth_service.validate_token('invalid_token')
