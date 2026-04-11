import pretend
import pytest
from pydantic import ValidationError

from repository_service_tuf_api import common_models
from repository_service_tuf_api.artifacts import ArtifactInfo
from repository_service_tuf_api.common_models import (
    TUFSignedDelegationsRoles,
    TUFSignedDelegationsSuccinctRoles,
    TUFSignedMetaFile,
    TUFSignedRoles,
)

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
        all_roles = [
            "root1",
            "1root",
            "root.json",
            "f",
            "bin",
            "bin0",
            "",
        ]
        for role in all_roles:
            assert common_models.Roles.is_role(role) is False

    def test_is_role_false_other_input(self):
        all_roles = [1, None, True, [], {}]
        for role in all_roles:
            assert common_models.Roles.is_role(role) is False


class TestTUFSignedDelegationsRolesThreshold:
    def test_threshold_valid(self):
        role = TUFSignedDelegationsRoles(
            name="test",
            terminating=False,
            keyids=["abc123"],
            threshold=1,
            paths=["*"],
        )
        assert role.threshold == 1

    def test_threshold_zero_rejected(self):
        with pytest.raises(ValidationError):
            TUFSignedDelegationsRoles(
                name="test",
                terminating=False,
                keyids=["abc123"],
                threshold=0,
                paths=["*"],
            )

    def test_threshold_negative_rejected(self):
        with pytest.raises(ValidationError):
            TUFSignedDelegationsRoles(
                name="test",
                terminating=False,
                keyids=["abc123"],
                threshold=-1,
                paths=["*"],
            )


class TestTUFSignedDelegationsSuccinctRolesThreshold:
    def test_threshold_valid(self):
        role = TUFSignedDelegationsSuccinctRoles(
            bit_length=4,
            name_prefix="bins",
            keyids=["abc123"],
            threshold=1,
        )
        assert role.threshold == 1

    def test_threshold_zero_rejected(self):
        with pytest.raises(ValidationError):
            TUFSignedDelegationsSuccinctRoles(
                bit_length=4,
                name_prefix="bins",
                keyids=["abc123"],
                threshold=0,
            )


class TestTUFSignedMetaFileVersion:
    def test_version_valid(self):
        meta = TUFSignedMetaFile(version=1)
        assert meta.version == 1

    def test_version_zero_rejected(self):
        with pytest.raises(ValidationError):
            TUFSignedMetaFile(version=0)

    def test_version_negative_rejected(self):
        with pytest.raises(ValidationError):
            TUFSignedMetaFile(version=-1)


class TestTUFSignedRolesThreshold:
    def test_threshold_valid(self):
        role = TUFSignedRoles(keyids=["abc123"], threshold=1)
        assert role.threshold == 1

    def test_threshold_zero_rejected(self):
        with pytest.raises(ValidationError):
            TUFSignedRoles(keyids=["abc123"], threshold=0)


class TestArtifactInfoLength:
    def test_length_valid_zero(self):
        info = ArtifactInfo(
            length=0,
            hashes={"sha256": "abc123"},
        )
        assert info.length == 0

    def test_length_valid_positive(self):
        info = ArtifactInfo(
            length=1024,
            hashes={"sha256": "abc123"},
        )
        assert info.length == 1024

    def test_length_negative_rejected(self):
        with pytest.raises(ValidationError):
            ArtifactInfo(
                length=-1,
                hashes={"sha256": "abc123"},
            )
