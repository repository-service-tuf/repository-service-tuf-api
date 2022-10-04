import pretend
from fastapi import status


class TestGetTask:
    def test_get(self, test_client, token_headers, monkeypatch):
        url = "/api/v1/task/"

        mocked_task_result = pretend.stub(
            state="SUCCESS", result={"status": "Task finished."}
        )
        mocked_repository_metadata = pretend.stub(
            AsyncResult=pretend.call_recorder(lambda t: mocked_task_result)
        )
        monkeypatch.setattr(
            "tuf_repository_service_api.tasks.repository_metadata",
            mocked_repository_metadata,
        )

        test_response = test_client.get(
            f"{url}?task_id=test_id", headers=token_headers
        )
        assert test_response.status_code == status.HTTP_200_OK
        assert test_response.json() == {
            "data": {
                "task_id": "test_id",
                "state": "SUCCESS",
                "result": {"status": "Task finished."},
            },
            "message": "Task state.",
        }
        assert mocked_repository_metadata.AsyncResult.calls == [
            pretend.call("test_id")
        ]

    def test_get_result_is_exception(
        self, test_client, token_headers, monkeypatch
    ):
        url = "/api/v1/task/"

        mocked_task_result = pretend.stub(
            state="SUCCESS", result=ValueError("Failed to load")
        )
        mocked_repository_metadata = pretend.stub(
            AsyncResult=pretend.call_recorder(lambda t: mocked_task_result)
        )
        monkeypatch.setattr(
            "tuf_repository_service_api.tasks.repository_metadata",
            mocked_repository_metadata,
        )

        test_response = test_client.get(
            f"{url}?task_id=test_id", headers=token_headers
        )
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

    def test_get_invalid_scope(self, test_client, monkeypatch):
        url = "/api/v1/task/"
        token_url = "/api/v1/token/?expires=1"
        token_payload = {
            "username": "admin",
            "password": "secret",
            "scope": ("read:targets " "read:settings " "read:token "),
        }
        token = test_client.post(token_url, data=token_payload)
        headers = {
            "Authorization": f"Bearer {token.json()['access_token']}",
        }

        test_response = test_client.get(
            f"{url}?task_id=test_id", headers=headers
        )
        assert test_response.status_code == status.HTTP_403_FORBIDDEN
        assert test_response.json() == {
            "detail": {"error": "scope 'read:tasks' not allowed"}
        }
