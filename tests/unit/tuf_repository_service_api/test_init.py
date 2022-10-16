# SPDX-FileCopyrightText: 2022 VMware Inc
#
# SPDX-License-Identifier: MIT

import pretend

import repository_service_tuf_api


class TestRestApi:
    def test_sync_redis(self):

        repository_service_tuf_api.settings_repository = pretend.stub(
            get=pretend.call_recorder(
                lambda *a: {"BOOTSTRAP": "fake_bootstrap_id"}
            )
        )

        fake_redis = pretend.stub(
            hgetall=pretend.call_recorder(
                lambda *a: {"BOOTSTRAP": "fake_bootstrap_id"}
            )
        )

        repository_service_tuf_api.redis_loader = pretend.stub(
            StrictRedis=pretend.call_recorder(lambda *a, **kw: fake_redis)
        )

        test_result = repository_service_tuf_api.sync_redis()
        assert test_result is None
        assert repository_service_tuf_api.redis_loader.StrictRedis.calls == [
            pretend.call(**{"BOOTSTRAP": "fake_bootstrap_id"})
        ]
        assert fake_redis.hgetall.calls == [pretend.call("DYNACONF_MAIN")]
        assert repository_service_tuf_api.settings_repository.get.calls == [
            pretend.call("BOOTSTRAP"),
            pretend.call("REDIS_FOR_DYNACONF"),
        ]

    def test_sync_redis_without_data(self):

        repository_service_tuf_api.settings_repository = pretend.stub(
            get=pretend.call_recorder(
                lambda *a: {"BOOTSTRAP": "fake_bootstrap_id"}
            ),
            to_dict=pretend.call_recorder(lambda: {"k": "v"}),
        )

        fake_redis = pretend.stub(hgetall=pretend.call_recorder(lambda *a: {}))
        repository_service_tuf_api.redis_loader = pretend.stub(
            StrictRedis=pretend.call_recorder(lambda *a, **kw: fake_redis),
            write=pretend.call_recorder(lambda *a: None),
        )

        test_result = repository_service_tuf_api.sync_redis()
        assert test_result is None
        assert repository_service_tuf_api.redis_loader.StrictRedis.calls == [
            pretend.call(**{"BOOTSTRAP": "fake_bootstrap_id"})
        ]
        assert fake_redis.hgetall.calls == [pretend.call("DYNACONF_MAIN")]
        assert repository_service_tuf_api.settings_repository.get.calls == [
            pretend.call("BOOTSTRAP"),
            pretend.call("REDIS_FOR_DYNACONF"),
        ]
        assert repository_service_tuf_api.redis_loader.write.calls == [
            pretend.call(
                repository_service_tuf_api.settings_repository, {"k": "v"}
            )
        ]
        assert (
            repository_service_tuf_api.settings_repository.to_dict.calls
            == [pretend.call()]
        )
