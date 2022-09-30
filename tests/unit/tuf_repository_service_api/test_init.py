import pretend

import tuf_repository_service_api


class TestRestApi:
    def test_sync_redis(self):

        tuf_repository_service_api.settings_repository = pretend.stub(
            get=pretend.call_recorder(
                lambda *a: {"BOOTSTRAP": "fake_bootstrap_id"}
            )
        )

        fake_redis = pretend.stub(
            hgetall=pretend.call_recorder(
                lambda *a: {"BOOTSTRAP": "fake_bootstrap_id"}
            )
        )

        tuf_repository_service_api.redis_loader = pretend.stub(
            StrictRedis=pretend.call_recorder(lambda *a, **kw: fake_redis)
        )

        test_result = tuf_repository_service_api.sync_redis()
        assert test_result is None
        assert tuf_repository_service_api.redis_loader.StrictRedis.calls == [
            pretend.call(**{"BOOTSTRAP": "fake_bootstrap_id"})
        ]
        assert fake_redis.hgetall.calls == [pretend.call("DYNACONF_MAIN")]
        assert tuf_repository_service_api.settings_repository.get.calls == [
            pretend.call("BOOTSTRAP"),
            pretend.call("REDIS_FOR_DYNACONF"),
        ]

    def test_sync_redis_without_data(self):

        tuf_repository_service_api.settings_repository = pretend.stub(
            get=pretend.call_recorder(
                lambda *a: {"BOOTSTRAP": "fake_bootstrap_id"}
            ),
            to_dict=pretend.call_recorder(lambda: {"k": "v"}),
        )

        fake_redis = pretend.stub(hgetall=pretend.call_recorder(lambda *a: {}))
        tuf_repository_service_api.redis_loader = pretend.stub(
            StrictRedis=pretend.call_recorder(lambda *a, **kw: fake_redis),
            write=pretend.call_recorder(lambda *a: None),
        )

        test_result = tuf_repository_service_api.sync_redis()
        assert test_result is None
        assert tuf_repository_service_api.redis_loader.StrictRedis.calls == [
            pretend.call(**{"BOOTSTRAP": "fake_bootstrap_id"})
        ]
        assert fake_redis.hgetall.calls == [pretend.call("DYNACONF_MAIN")]
        assert tuf_repository_service_api.settings_repository.get.calls == [
            pretend.call("BOOTSTRAP"),
            pretend.call("REDIS_FOR_DYNACONF"),
        ]
        assert tuf_repository_service_api.redis_loader.write.calls == [
            pretend.call(
                tuf_repository_service_api.settings_repository, {"k": "v"}
            )
        ]
        assert (
            tuf_repository_service_api.settings_repository.to_dict.calls
            == [pretend.call()]
        )
