import json
from uuid import uuid4

import pretend
from fastapi import status


class TestPostTargets:
    def test_post(self, monkeypatch, test_client):
        from kaprien_api import simple_settings  # noqa

        url = "/api/v1/targets/"
        with open("tests/data_examples/targets/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)
        mocked_repository_metadata = pretend.stub(
            apply_async=pretend.call_recorder(lambda *a, **kw: None)
        )
        fake_task_id = uuid4().hex
        monkeypatch.setattr(
            "kaprien_api.targets.repository_metadata",
            mocked_repository_metadata,
        )
        monkeypatch.setattr(
            "kaprien_api.targets.task_id", lambda: fake_task_id
        )
        response = test_client.post(url, json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": {
                "targets": ["file1.tar.gz", "file2.tar.gz"],
                "task_id": fake_task_id,
            },
            "message": "Target(s) successfully submitted.",
        }
        assert mocked_repository_metadata.apply_async.calls == [
            pretend.call(
                kwargs={
                    "action": "add_targets",
                    "settings": simple_settings.to_dict(),
                    "payload": payload,
                },
                task_id=fake_task_id,
                queue="metadata_repository",
            )
        ]

    def test_post_missing_required_field(self, test_client):
        url = "/api/v1/targets/"
        payload = {
            "targets": [
                {
                    "info": {
                        "length": 11342,
                        "custom": {"key": "value"},
                    },
                }
            ]
        }

        response = test_client.post(url, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
