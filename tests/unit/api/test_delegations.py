# SPDX-FileCopyrightText: 2025 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

import json

import pretend
from fastapi import status

from repository_service_tuf_api import BootstrapState

DELEGATIONS_URL = "/api/v1/delegations/"
DELEGATIONS_DELETE_URL = "/api/v1/delegations/delete"
MOCK_PATH = "repository_service_tuf_api.delegations"


class TestPostDelegationAPI:
    def test_post_delegation(self, test_client, monkeypatch, fake_datetime):
        """Test creating a new delegation via POST /api/v1/delegations/"""
        # Mock bootstrap_state to return a bootstrapped state
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state",
            pretend.call_recorder(
                lambda: BootstrapState(bootstrap=True, state="FINISHED")
            ),
        )

        # Mock get_task_id to return a deterministic task ID
        monkeypatch.setattr(
            f"{MOCK_PATH}.get_task_id",
            pretend.call_recorder(lambda: "fake_task_id"),
        )

        # Mock repository_metadata.apply_async
        mock_apply_async = pretend.call_recorder(lambda **kw: None)
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata",
            pretend.stub(apply_async=mock_apply_async),
        )

        # Mock datetime
        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)

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

        # Verify mocks were called correctly
        assert mock_apply_async.calls
        call_kwargs = mock_apply_async.calls[0].kwargs
        assert call_kwargs["task_id"] == "fake_task_id"
        assert call_kwargs["queue"] == "metadata_repository"
        assert call_kwargs["kwargs"]["action"] == "metadata_delegation"
        assert call_kwargs["kwargs"]["payload"]["action"] == "add"

    def test_post_delegation_no_bootstrap(self, test_client, monkeypatch):
        """Test error case when bootstrap is not complete"""
        # Mock bootstrap_state to return a non-bootstrapped state
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state",
            pretend.call_recorder(
                lambda: BootstrapState(bootstrap=False, state="PRE")
            ),
        )

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
        # Mock bootstrap_state to return a bootstrapped state
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state",
            pretend.call_recorder(
                lambda: BootstrapState(bootstrap=True, state="FINISHED")
            ),
        )

        # Mock get_task_id to return a deterministic task ID
        monkeypatch.setattr(
            f"{MOCK_PATH}.get_task_id",
            pretend.call_recorder(lambda: "fake_task_id"),
        )

        # Mock repository_metadata.apply_async
        mock_apply_async = pretend.call_recorder(lambda **kw: None)
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata",
            pretend.stub(apply_async=mock_apply_async),
        )

        # Mock datetime
        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)

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

        # Verify mocks were called correctly
        assert mock_apply_async.calls
        call_kwargs = mock_apply_async.calls[0].kwargs
        assert call_kwargs["task_id"] == "fake_task_id"
        assert call_kwargs["queue"] == "metadata_repository"
        assert call_kwargs["kwargs"]["action"] == "metadata_delegation"
        assert call_kwargs["kwargs"]["payload"]["action"] == "update"

    def test_put_delegation_no_bootstrap(self, test_client, monkeypatch):
        """Test error case when bootstrap is not complete"""
        # Mock bootstrap_state to return a non-bootstrapped state
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state",
            pretend.call_recorder(
                lambda: BootstrapState(bootstrap=False, state="PRE")
            ),
        )

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
        # Mock bootstrap_state to return a bootstrapped state
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state",
            pretend.call_recorder(
                lambda: BootstrapState(bootstrap=True, state="FINISHED")
            ),
        )

        # Mock get_task_id to return a deterministic task ID
        monkeypatch.setattr(
            f"{MOCK_PATH}.get_task_id",
            pretend.call_recorder(lambda: "fake_task_id"),
        )

        # Mock repository_metadata.apply_async
        mock_apply_async = pretend.call_recorder(lambda **kw: None)
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata",
            pretend.stub(apply_async=mock_apply_async),
        )

        # Mock datetime
        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)

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

        # Verify mocks were called correctly
        assert mock_apply_async.calls
        call_kwargs = mock_apply_async.calls[0].kwargs
        assert call_kwargs["task_id"] == "fake_task_id"
        assert call_kwargs["queue"] == "metadata_repository"
        assert call_kwargs["kwargs"]["action"] == "metadata_delegation"
        assert call_kwargs["kwargs"]["payload"]["action"] == "delete"

    def test_delete_delegation_no_bootstrap(self, test_client, monkeypatch):
        """Test error case when bootstrap is not complete"""
        # Mock bootstrap_state to return a non-bootstrapped state
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state",
            pretend.call_recorder(
                lambda: BootstrapState(bootstrap=False, state="PRE")
            ),
        )

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
