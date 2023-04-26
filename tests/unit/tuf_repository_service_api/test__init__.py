# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
import pretend
import repository_service_tuf_api


class TestInit:
    def test_is_bootstrap_done_none(self):
        repository_service_tuf_api.settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: None)
        )

        result = repository_service_tuf_api.is_bootstrap_done()
        assert result is False

    def test_is_bootstrap_done_with_task_id(self):
        repository_service_tuf_api.settings_repository = pretend.stub(
            reload=pretend.call_recorder(lambda: None),
            get_fresh=pretend.call_recorder(lambda *a: "taskid")
        )

        result = repository_service_tuf_api.is_bootstrap_done()
        assert result is True


