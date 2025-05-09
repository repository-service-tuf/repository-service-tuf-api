# SPDX-FileCopyrightText: 2024 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

import json
from datetime import timezone

import pretend
from fastapi import status

DELEGATIONS_URL = "/api/v1/delegations/"
DELEGATIONS_DELETE_URL = "/api/v1/delegations/delete"
MOCK_PATH = "repository_service_tuf_api.delegations"


class TestPostDelegationAPI:
    def test_post_delegation(self, test_client, monkeypatch, fake_datetime):
        """Test creating a new delegation via POST /api/v1/delegations/"""
        # Mock metadata_delegation function
        mocked_delegation_response = pretend.stub(
            data=pretend.stub(
                task_id="fake_task_id",
                last_update=fake_datetime.now(timezone.utc),
            ),
            message="Metadata delegation add accepted.",
        )
        mocked_metadata_delegation = pretend.call_recorder(
            lambda payload, action: mocked_delegation_response
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.metadata_delegation", mocked_metadata_delegation
        )

        # Load test payload
        with open("tests/data_examples/metadata/delegation-payload.json") as f:
            payload = json.loads(f.read())

        # Make API request
        response = test_client.post(DELEGATIONS_URL, json=payload)

        # Verify response
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.url == f"{test_client.base_url}{DELEGATIONS_URL}"
        assert (
            response.json()["message"] == "Metadata delegation add accepted."
        )
        assert response.json()["data"]["task_id"] == "fake_task_id"

        # Verify mock was called correctly
        assert len(mocked_metadata_delegation.calls) == 1
        # Check that the function was called (without checking specific args)
        assert mocked_metadata_delegation.calls

    def test_post_delegation_no_bootstrap(self, test_client, monkeypatch):
        """Test error case when bootstrap is not complete"""
        # Mock metadata_delegation to raise HTTPException
        from fastapi import HTTPException

        def mock_error(*args, **kwargs):
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail={
                    "message": "Task not accepted.",
                    "error": "Requires bootstrap finished. State: PRE",
                },
            )

        monkeypatch.setattr(f"{MOCK_PATH}.metadata_delegation", mock_error)

        # Load test payload
        with open("tests/data_examples/metadata/delegation-payload.json") as f:
            payload = json.loads(f.read())

        # Make API request
        response = test_client.post(DELEGATIONS_URL, json=payload)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.json()
        assert "message" in response.json()["detail"]
        assert response.json()["detail"]["message"] == "Task not accepted."
        assert (
            "Requires bootstrap finished" in response.json()["detail"]["error"]
        )


class TestPutDelegationAPI:
    def test_put_delegation(self, test_client, monkeypatch, fake_datetime):
        """Test updating a delegation via PUT /api/v1/delegations/"""
        # Mock metadata_delegation function
        mocked_delegation_response = pretend.stub(
            data=pretend.stub(
                task_id="fake_task_id",
                last_update=fake_datetime.now(timezone.utc),
            ),
            message="Metadata delegation update accepted.",
        )
        mocked_metadata_delegation = pretend.call_recorder(
            lambda payload, action: mocked_delegation_response
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.metadata_delegation", mocked_metadata_delegation
        )

        # Load test payload
        with open("tests/data_examples/metadata/delegation-payload.json") as f:
            payload = json.loads(f.read())

        # Make API request
        response = test_client.put(DELEGATIONS_URL, json=payload)

        # Verify response
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.url == f"{test_client.base_url}{DELEGATIONS_URL}"
        assert (
            response.json()["message"]
            == "Metadata delegation update accepted."
        )
        assert response.json()["data"]["task_id"] == "fake_task_id"

        # Verify mock was called correctly
        assert len(mocked_metadata_delegation.calls) == 1
        # Check that the function was called (without checking specific args)
        assert mocked_metadata_delegation.calls

    def test_put_delegation_no_bootstrap(self, test_client, monkeypatch):
        """Test error case when bootstrap is not complete"""
        # Mock metadata_delegation to raise HTTPException
        from fastapi import HTTPException

        def mock_error(*args, **kwargs):
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail={
                    "message": "Task not accepted.",
                    "error": "Requires bootstrap finished. State: PRE",
                },
            )

        monkeypatch.setattr(f"{MOCK_PATH}.metadata_delegation", mock_error)

        # Load test payload
        with open("tests/data_examples/metadata/delegation-payload.json") as f:
            payload = json.loads(f.read())

        # Make API request
        response = test_client.put(DELEGATIONS_URL, json=payload)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.json()
        assert "message" in response.json()["detail"]
        assert response.json()["detail"]["message"] == "Task not accepted."
        assert (
            "Requires bootstrap finished" in response.json()["detail"]["error"]
        )


class TestDeleteDelegationAPI:
    def test_delete_delegation(self, test_client, monkeypatch, fake_datetime):
        """Test deleting a delegation via POST /api/v1/delegations/delete"""
        # Mock metadata_delegation function
        mocked_delegation_response = pretend.stub(
            data=pretend.stub(
                task_id="fake_task_id",
                last_update=fake_datetime.now(timezone.utc),
            ),
            message="Metadata delegation delete accepted.",
        )
        mocked_metadata_delegation = pretend.call_recorder(
            lambda payload, action: mocked_delegation_response
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.metadata_delegation", mocked_metadata_delegation
        )

        # Create delete payload
        payload = {"delegations": {"roles": [{"name": "dev"}]}}

        # Make API request
        response = test_client.post(DELEGATIONS_DELETE_URL, json=payload)

        # Verify response
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert (
            response.url == f"{test_client.base_url}{DELEGATIONS_DELETE_URL}"
        )
        assert (
            response.json()["message"]
            == "Metadata delegation delete accepted."
        )
        assert response.json()["data"]["task_id"] == "fake_task_id"

        # Verify mock was called correctly
        assert len(mocked_metadata_delegation.calls) == 1
        # Check that the function was called (without checking specific args)
        assert mocked_metadata_delegation.calls

    def test_delete_delegation_no_bootstrap(self, test_client, monkeypatch):
        """Test error case when bootstrap is not complete"""
        # Mock metadata_delegation to raise HTTPException
        from fastapi import HTTPException

        def mock_error(*args, **kwargs):
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail={
                    "message": "Task not accepted.",
                    "error": "Requires bootstrap finished. State: PRE",
                },
            )

        monkeypatch.setattr(f"{MOCK_PATH}.metadata_delegation", mock_error)

        # Create delete payload
        payload = {"delegations": {"roles": [{"name": "dev"}]}}

        # Make API request
        response = test_client.post(DELEGATIONS_DELETE_URL, json=payload)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.json()
        assert "message" in response.json()["detail"]
        assert response.json()["detail"]["message"] == "Task not accepted."
        assert (
            "Requires bootstrap finished" in response.json()["detail"]["error"]
        )
