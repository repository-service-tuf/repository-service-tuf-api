import json

from fastapi import status


class TestPostTargets:
    def test_post(self, test_client):
        url = "/api/v1/targets/"
        with open("tests/data_examples/targets/payload.json") as f:
            f_data = f.read()

        payload = json.loads(f_data)

        response = test_client.post(url, json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": ["file1.tar.gz", "file2.tar.gz"],
            "message": "Target file(s) successfully added.",
        }

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
