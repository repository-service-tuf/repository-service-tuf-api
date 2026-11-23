import pretend

from repository_service_tuf_api import common_models

COMMON_MODELS_PATH = "repository_service_tuf_api.common_models"


class TestRoles:
    def test_online_values_all_true(self, monkeypatch):
        def fake_get_fresh(args: str):
            setting = args[0]
            if setting == "TARGETS_ONLINE_KEY":
                return True
            elif setting == "DELEGATED_ROLES_NAMES":
                return ["bins-0", "bins-1"]

        mocked_settings_repository = pretend.stub(
            get_fresh=pretend.call_recorder(lambda *a: fake_get_fresh(a)),
        )
        monkeypatch.setattr(
            f"{COMMON_MODELS_PATH}.settings_repository",
            mocked_settings_repository,
        )

        result = common_models.Roles.online_roles_values()
        assert result == ["snapshot", "timestamp", "targets", "bins"]
        assert mocked_settings_repository.get_fresh.calls == [
            pretend.call("TARGETS_ONLINE_KEY", True),
            pretend.call("DELEGATED_ROLES_NAMES"),
        ]

    def test_online_values_custom_delegations(self, monkeypatch):
        def fake_get_fresh(args: str):
            setting = args[0]
            if setting == "TARGETS_ONLINE_KEY":
                return True
            elif setting == "DELEGATED_ROLES_NAMES":
                return ["foo", "bar"]

        mocked_settings_repository = pretend.stub(
            get_fresh=pretend.call_recorder(lambda *a: fake_get_fresh(a)),
        )
        monkeypatch.setattr(
            f"{COMMON_MODELS_PATH}.settings_repository",
            mocked_settings_repository,
        )

        result = common_models.Roles.online_roles_values()
        assert result == ["snapshot", "timestamp", "targets", "foo", "bar"]
        assert mocked_settings_repository.get_fresh.calls == [
            pretend.call("TARGETS_ONLINE_KEY", True),
            pretend.call("DELEGATED_ROLES_NAMES"),
        ]

    def test_getting_online_values_targets_role_is_offline(self, monkeypatch):
        def fake_get_fresh(args: str):
            setting = args[0]
            if setting == "TARGETS_ONLINE_KEY":
                return False
            elif setting == "DELEGATED_ROLES_NAMES":
                return ["bins-0", "bins-1"]

        mocked_settings_repository = pretend.stub(
            get_fresh=pretend.call_recorder(lambda *a: fake_get_fresh(a)),
        )
        monkeypatch.setattr(
            f"{COMMON_MODELS_PATH}.settings_repository",
            mocked_settings_repository,
        )

        result = common_models.Roles.online_roles_values()
        assert result == ["snapshot", "timestamp", "bins"]
        assert mocked_settings_repository.get_fresh.calls == [
            pretend.call("TARGETS_ONLINE_KEY", True),
            pretend.call("DELEGATED_ROLES_NAMES"),
        ]

    def test_is_role_true_all_roles(self):
        all = ["root", "targets", "snapshot", "timestamp", "bins"]
        for role in all:
            assert common_models.Roles.is_role(role) is True

    def test_is_role_false_str(self):
        all_roles = ["root1", "1root", "root.json", "f", "bin", "bin0", ""]
        for role in all_roles:
            assert common_models.Roles.is_role(role) is False

    def test_is_role_false_other_input(self):
        all_roles = [1, None, True, [], {}]
        for role in all_roles:
            assert common_models.Roles.is_role(role) is False
import pytest
from repository_service_tuf_api.common_models import TUFSignedDelegationsRoles, TUFSigned

def test_tuf_signed_delegations_roles_paths_validation():
    with pytest.raises(ValueError, match="No empty strings are allowed as path patterns"):
        TUFSignedDelegationsRoles(
            name="test",
            public_keys=["key1"],
            paths=["valid", ""]
        )

def test_tuf_signed_unrecognized_fields():
    TUFSigned(
        _type="Root",
        spec_version="1.0.0",
        version=1,
        expires="2020-01-01T00:00:00Z",
        keys={},
        roles={},
        **{"x-vendor-name": "valid"}
    )
    with pytest.raises(ValueError, match="unrecognized_field must use format x-<vendor>-<name>"):
        TUFSigned(
            _type="Root",
            spec_version="1.0.0",
            version=1,
            expires="2020-01-01T00:00:00Z",
            keys={},
            roles={},
            **{"invalid-field": "value"}
        )


def test_tuf_signed_delegations_roles_paths_validation_valid():
    from repository_service_tuf_api.common_models import TUFSignedDelegationsRoles, Roles
    
    # Valid paths (covers line 90)
    TUFSignedDelegationsRoles(
        name="test",
        keyids=["key1"],
        threshold=1,
        terminating=False,
        paths=["valid"]
    )
    
    # Covers line 30
    assert Roles.all_str() == "root, targets, snapshot, timestamp and bins"
