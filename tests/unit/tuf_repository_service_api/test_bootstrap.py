# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
import pretend

from repository_service_tuf_api import bootstrap


class TestBootstrap:
    def test__check_bootstrap_status_SUCCESS(self):
        bootstrap.repository_metadata.AsyncResult = pretend.call_recorder(
            lambda *a: pretend.stub(status="SUCCESS")
        )

        result = bootstrap._check_bootstrap_status("fake_task_id", 2)

        assert result is None
        assert bootstrap.repository_metadata.AsyncResult.calls == [
            pretend.call("fake_task_id")
        ]

    def test__check_bootstrap_status_FAILURE(self):
        bootstrap.repository_metadata.AsyncResult = pretend.call_recorder(
            lambda *a: pretend.stub(status="FAILURE")
        )
        bootstrap.release_bootstrap_lock = pretend.call_recorder(lambda: None)

        result = bootstrap._check_bootstrap_status("fake_task_id", 2)

        assert result is None
        assert bootstrap.repository_metadata.AsyncResult.calls == [
            pretend.call("fake_task_id")
        ]
        assert bootstrap.release_bootstrap_lock.calls == [pretend.call()]

    def test__check_bootstrap_status_timeout(self):
        fake_task = pretend.stub(
            status="STARTED",
            revoke=pretend.call_recorder(lambda **kw: None),
        )
        bootstrap.repository_metadata.AsyncResult = pretend.call_recorder(
            lambda *a: fake_task
        )
        bootstrap.release_bootstrap_lock = pretend.call_recorder(lambda: None)

        result = bootstrap._check_bootstrap_status("fake_task_id", 2)

        assert result is None
        assert len(bootstrap.repository_metadata.AsyncResult.calls) > 1
        assert fake_task.revoke.calls == [pretend.call(terminate=True)]
        assert bootstrap.release_bootstrap_lock.calls == [pretend.call()]

    def test_get_bootstrap_none(self):
        bootstrap.is_bootstrap_done = pretend.call_recorder(lambda: None)
        bootstrap.get_bootstrap() == bootstrap.BootstrapGetResponse(
            data=bootstrap.GetData(bootstrap=False, state=None),
            message="System available for bootstrap.",
        )

    def test_get_bootstrap_pre(self):
        bootstrap.is_bootstrap_done = pretend.call_recorder(
            lambda: "pre-fakeid"
        )
        bootstrap.get_bootstrap() == bootstrap.BootstrapGetResponse(
            data=bootstrap.GetData(bootstrap=False, state="pre"),
            message="System LOCKED for bootstrap.",
        )

    def test_get_bootstrap_finished(self):
        bootstrap.is_bootstrap_done = pretend.call_recorder(lambda: "fakeid")
        bootstrap.get_bootstrap() == bootstrap.BootstrapGetResponse(
            data=bootstrap.GetData(bootstrap=False, state="finished"),
            message="System LOCKED for bootstrap.",
        )
