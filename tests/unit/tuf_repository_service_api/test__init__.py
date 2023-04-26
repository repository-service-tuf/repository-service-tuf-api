# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
import pretend

import repository_service_tuf_api


class TestInit:
    def test_is_bootstrap_done_none(self):
        repository_service_tuf_api.settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: None),
        )

        result = repository_service_tuf_api.is_bootstrap_done()
        assert result is False

    def test_is_bootstrap_done_with_task_id(self):
        repository_service_tuf_api.settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: "taskid"),
        )

        result = repository_service_tuf_api.is_bootstrap_done()
        assert result is True

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
