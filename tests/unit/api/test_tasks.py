# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import pretend
from fastapi import status


class TestGetTask:
    def test_get(self, test_client, monkeypatch):
        url = "/api/v1/task/"

        mocked_task_result = pretend.stub(
            state="SUCCESS",
            result={
                "status": True,
                "task": "add_targets",
                "last_update": "2023-11-17T09:54:15.762882",
                "details": {"message": "Target(s) Added"},
            },
        )
        mocked_repository_metadata = pretend.stub(
            AsyncResult=pretend.call_recorder(lambda t: mocked_task_result)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.tasks.repository_metadata",
            mocked_repository_metadata,
        )

        test_response = test_client.get(f"{url}?task_id=test_id")
        assert test_response.status_code == status.HTTP_200_OK
        assert test_response.json() == {
            "data": {
                "task_id": "test_id",
                "state": "SUCCESS",
                "result": {
                    "status": True,
                    "task": "add_targets",
                    "last_update": "2023-11-17T09:54:15.762882",
                    "details": {"message": "Target(s) Added"},
                },
            },
            "message": "Task state.",
        }
        assert mocked_repository_metadata.AsyncResult.calls == [
            pretend.call("test_id")
        ]

    def test_get_result_is_exception(self, test_client, monkeypatch):
        url = "/api/v1/task/"

        mocked_task_result = pretend.stub(
            state="SUCCESS", result=ValueError("Failed to load")
        )
        mocked_repository_metadata = pretend.stub(
            AsyncResult=pretend.call_recorder(lambda t: mocked_task_result)
        )
        monkeypatch.setattr(
            "repository_service_tuf_api.tasks.repository_metadata",
            mocked_repository_metadata,
        )

        test_response = test_client.get(f"{url}?task_id=test_id")
        assert test_response.status_code == status.HTTP_200_OK
        assert test_response.json() == {
            "data": {
                "task_id": "test_id",
                "state": "SUCCESS",
                "result": "Failed to load",
            },
            "message": "Task state.",
        }
        assert mocked_repository_metadata.AsyncResult.calls == [
            pretend.call("test_id")
        ]
