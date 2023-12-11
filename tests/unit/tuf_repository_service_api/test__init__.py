# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
import pretend

import repository_service_tuf_api


class TestInit:
    def test_pre_lock_bootstrap(self):
        fake_settings = pretend.stub(
            current_env="test", as_dict=pretend.call_recorder(lambda **kw: {})
        )
        repository_service_tuf_api.settings_repository = fake_settings
        repository_service_tuf_api.redis_loader.write = pretend.call_recorder(
            lambda *a: fake_settings
        )

        repository_service_tuf_api.pre_lock_bootstrap("fake_task_id")

        assert fake_settings.as_dict.calls == [pretend.call(env="test")]
        assert repository_service_tuf_api.redis_loader.write.calls == [
            pretend.call(fake_settings, {"BOOTSTRAP": "pre-fake_task_id"})
        ]

    def test_release_bootstrap_lock(self):
        fake_settings = pretend.stub(
            current_env="test", as_dict=pretend.call_recorder(lambda **kw: {})
        )
        repository_service_tuf_api.settings_repository = fake_settings
        repository_service_tuf_api.redis_loader.write = pretend.call_recorder(
            lambda *a: fake_settings
        )

        repository_service_tuf_api.release_bootstrap_lock()

        assert fake_settings.as_dict.calls == [pretend.call(env="test")]
        assert repository_service_tuf_api.redis_loader.write.calls == [
            pretend.call(fake_settings, {"BOOTSTRAP": None})
        ]

    def test_bootstrap_state(self):
        repository_service_tuf_api.settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: None),
        )
        result = repository_service_tuf_api.bootstrap_state()
        assert result == repository_service_tuf_api.BootstrapState(
            False, None, None
        )

    def test_bootstrap_state_pre(self):
        repository_service_tuf_api.settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: "pre-<task_id>"),
        )
        result = repository_service_tuf_api.bootstrap_state()
        assert result == repository_service_tuf_api.BootstrapState(
            False, "pre", "<task_id>"
        )

    def test_bootstrap_state_signing(self):
        repository_service_tuf_api.settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: "signing-<task_id>"),
        )
        result = repository_service_tuf_api.bootstrap_state()
        assert result == repository_service_tuf_api.BootstrapState(
            False, "signing", "<task_id>"
        )

    def test_bootstrap_state_finished(self):
        repository_service_tuf_api.settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: "<task_id>"),
        )
        result = repository_service_tuf_api.bootstrap_state()
        assert result == repository_service_tuf_api.BootstrapState(
            True, "finished", "<task_id>"
        )
