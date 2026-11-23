import logging
from uuid import uuid4

import pretend

from repository_service_tuf_api import (
    BootstrapState,
    bootstrap_state,
    get_task_id,
    pre_lock_bootstrap,
    release_bootstrap_lock,
    repository_metadata,
)

class TestInit:
    def test_pre_lock_bootstrap(self, monkeypatch):
        mock_settings_repository = pretend.stub(
            as_dict=pretend.call_recorder(lambda env: {"BOOTSTRAP": None}),
            current_env="test_env",
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.settings_repository",
            mock_settings_repository,
        )

        mock_redis_loader = pretend.stub(
            write=pretend.call_recorder(lambda settings, data: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.redis_loader", mock_redis_loader
        )

        task_id = "testtask123"
        pre_lock_bootstrap(task_id)

        assert mock_settings_repository.as_dict.calls == [
            pretend.call(env="test_env")
        ]
        assert mock_redis_loader.write.calls == [
            pretend.call(
                mock_settings_repository,
                {"BOOTSTRAP": f"pre-{task_id}"},
            )
        ]

    def test_release_bootstrap_lock(self, monkeypatch):
        mock_settings_repository = pretend.stub(
            as_dict=pretend.call_recorder(lambda env: {"BOOTSTRAP": "pre-123"}),
            current_env="test_env",
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.settings_repository",
            mock_settings_repository,
        )

        mock_redis_loader = pretend.stub(
            write=pretend.call_recorder(lambda settings, data: None)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.redis_loader", mock_redis_loader
        )

        release_bootstrap_lock()

        assert mock_settings_repository.as_dict.calls == [
            pretend.call(env="test_env")
        ]
        assert mock_redis_loader.write.calls == [
            pretend.call(
                mock_settings_repository,
                {"BOOTSTRAP": None},
            )
        ]

    def test_bootstrap_state_none(self, monkeypatch):
        mock_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda key: None),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.settings_repository",
            mock_settings_repository,
        )

        state = bootstrap_state()

        assert mock_settings_repository.reload.calls == [pretend.call()]
        assert mock_settings_repository.get_fresh.calls == [
            pretend.call("BOOTSTRAP")
        ]
        assert state == BootstrapState(
            bootstrap=False, state=None, task_id=None
        )

    def test_bootstrap_state_finished(self, monkeypatch):
        task_id = "testtask123"
        mock_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda key: task_id),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.settings_repository",
            mock_settings_repository,
        )

        state = bootstrap_state()

        assert mock_settings_repository.reload.calls == [pretend.call()]
        assert mock_settings_repository.get_fresh.calls == [
            pretend.call("BOOTSTRAP")
        ]
        assert state == BootstrapState(
            bootstrap=True, state="finished", task_id=task_id
        )

    def test_bootstrap_state_intermediate(self, monkeypatch):
        task_id = "testtask123"
        mock_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda key: f"signing-{task_id}"),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.settings_repository",
            mock_settings_repository,
        )

        state = bootstrap_state()

        assert mock_settings_repository.reload.calls == [pretend.call()]
        assert mock_settings_repository.get_fresh.calls == [
            pretend.call("BOOTSTRAP")
        ]
        assert state == BootstrapState(
            bootstrap=False, state="signing", task_id=task_id
        )

    def test_bootstrap_state_unexpected(self, monkeypatch):
        mock_settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda key: "a-b-c"),
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.settings_repository",
            mock_settings_repository,
        )

        mock_logging = pretend.stub(
            warning=pretend.call_recorder(lambda msg: None)
        )
        monkeypatch.setattr("repository_service_tuf_api.logging", mock_logging)

        state = bootstrap_state()

        assert mock_settings_repository.reload.calls == [pretend.call()]
        assert mock_settings_repository.get_fresh.calls == [
            pretend.call("BOOTSTRAP")
        ]
        assert mock_logging.warning.calls == [
            pretend.call("Unexpected bootstrap value format: 'a-b-c'")
        ]
        assert state == BootstrapState(
            bootstrap=False, state="unknown", task_id=None
        )

    def test_get_task_id(self, monkeypatch):
        fake_uuid = "fake-uuid-1234"
        mock_uuid4 = pretend.call_recorder(
            lambda: pretend.stub(hex=fake_uuid)
        )
        monkeypatch.setattr("repository_service_tuf_api.uuid4", mock_uuid4)

        result = get_task_id()

        assert mock_uuid4.calls == [pretend.call()]
        assert result == fake_uuid

    def test_repository_metadata(self, monkeypatch):
        mock_logging = pretend.stub(
            debug=pretend.call_recorder(lambda msg: None)
        )
        monkeypatch.setattr("repository_service_tuf_api.logging", mock_logging)

        result = repository_metadata("test_action", {"test": "payload"})

        assert mock_logging.debug.calls == [
            pretend.call("New tasks action submitted test_action")
        ]
        assert result is True
