from typing import Literal

import pretend

from repository_service_tuf_api import common_models

COMMON_MODELS_PATH = "repository_service_tuf_api.common_models"


class TestRoles:
    def test_getting_online_values(self, monkeypatch):
        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: True),
        )
        monkeypatch.setattr(
            f"{COMMON_MODELS_PATH}.settings_repository",
            mocked_settings_repository,
        )

        result = common_models.Roles.online_roles_values()
        assert result == Literal["targets", "snapshot", "timestamp", "bins"]
        assert mocked_settings_repository.reload.calls == [pretend.call()]
        assert mocked_settings_repository.get_fresh.calls == [
            pretend.call("TARGETS_ONLINE_KEY", True)
        ]

    def test_getting_online_values_targets_role_is_offline(self, monkeypatch):
        mocked_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: False),
        )
        monkeypatch.setattr(
            f"{COMMON_MODELS_PATH}.settings_repository",
            mocked_settings_repository,
        )

        result = common_models.Roles.online_roles_values()
        assert result == Literal["snapshot", "timestamp", "bins"]
        assert mocked_settings_repository.reload.calls == [pretend.call()]
        assert mocked_settings_repository.get_fresh.calls == [
            pretend.call("TARGETS_ONLINE_KEY", True)
        ]
