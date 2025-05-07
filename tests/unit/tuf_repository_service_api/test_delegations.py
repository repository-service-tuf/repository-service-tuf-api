# SPDX-FileCopyrightText: 2024 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT
import pretend
from fastapi import HTTPException

from repository_service_tuf_api.delegations import metadata_delegation


class TestDelegations:
    """Tests for the critical aspects of metadata delegation functionality."""

    def test_metadata_delegation_no_bootstrap(self):
        """Test when bootstrap is not finished."""
        # Mock bootstrap_state
        orig_bootstrap_state = metadata_delegation.__globals__[
            "bootstrap_state"
        ]
        metadata_delegation.__globals__["bootstrap_state"] = (
            lambda: pretend.stub(bootstrap=False, state="PRE")
        )

        # Create test payload
        payload = pretend.stub()

        try:
            # Use a try/except to handle the HTTPException
            raised_exception = None
            try:
                metadata_delegation(payload, "delete")
            except HTTPException as exc:
                raised_exception = exc

            # Verify exception details
            assert raised_exception is not None
            assert raised_exception.status_code == 200
            assert (
                "Requires bootstrap finished"
                in raised_exception.detail["error"]
            )
        finally:
            # Restore original
            metadata_delegation.__globals__["bootstrap_state"] = (
                orig_bootstrap_state
            )

    def test_metadata_delegation_success(self):
        """Test successful delegation add operation."""
        # Save original functions
        orig_bootstrap_state = metadata_delegation.__globals__[
            "bootstrap_state"
        ]
        orig_get_task_id = metadata_delegation.__globals__["get_task_id"]
        orig_repository_metadata = metadata_delegation.__globals__[
            "repository_metadata"
        ]

        # Mock bootstrap_state
        metadata_delegation.__globals__["bootstrap_state"] = (
            lambda: pretend.stub(bootstrap=True, state="FINISHED")
        )

        # Mock get_task_id
        metadata_delegation.__globals__["get_task_id"] = lambda: "fake_task_id"

        # Mock repository_metadata
        mock_apply_async = pretend.call_recorder(lambda **kw: None)
        metadata_delegation.__globals__["repository_metadata"] = pretend.stub(
            apply_async=mock_apply_async
        )

        # Create test payload
        payload = pretend.stub(model_dump=lambda **kw: {"test": "data"})

        try:
            # Call the function
            response = metadata_delegation(payload, "add")

            # Verify response
            assert response.data.task_id == "fake_task_id"
            assert "Metadata delegation add accepted" in response.message

            # Verify mock was called
            assert len(mock_apply_async.calls) == 1
            call_kwargs = mock_apply_async.calls[0].kwargs
            assert call_kwargs["task_id"] == "fake_task_id"
            assert call_kwargs["queue"] == "metadata_repository"
            assert call_kwargs["kwargs"]["action"] == "metadata_delegation"
        finally:
            # Restore original functions
            metadata_delegation.__globals__["bootstrap_state"] = (
                orig_bootstrap_state
            )
            metadata_delegation.__globals__["get_task_id"] = orig_get_task_id
            metadata_delegation.__globals__["repository_metadata"] = (
                orig_repository_metadata
            )

    def test_metadata_delegation_delete(self):
        """Test successful delegation delete operation."""
        # Save original functions
        orig_bootstrap_state = metadata_delegation.__globals__[
            "bootstrap_state"
        ]
        orig_get_task_id = metadata_delegation.__globals__["get_task_id"]
        orig_repository_metadata = metadata_delegation.__globals__[
            "repository_metadata"
        ]

        # Mock bootstrap_state
        metadata_delegation.__globals__["bootstrap_state"] = (
            lambda: pretend.stub(bootstrap=True, state="FINISHED")
        )

        # Mock get_task_id
        metadata_delegation.__globals__["get_task_id"] = lambda: "fake_task_id"

        # Mock repository_metadata
        mock_apply_async = pretend.call_recorder(lambda **kw: None)
        metadata_delegation.__globals__["repository_metadata"] = pretend.stub(
            apply_async=mock_apply_async
        )

        # Create test payload
        payload = pretend.stub(
            model_dump=lambda **kw: {
                "delegations": {"roles": [{"name": "dev"}]}
            }
        )

        try:
            # Call the function
            response = metadata_delegation(payload, "delete")

            # Verify response
            assert response.data.task_id == "fake_task_id"
            assert "Metadata delegation delete accepted" in response.message

            # Verify mock was called
            assert len(mock_apply_async.calls) == 1
            call_kwargs = mock_apply_async.calls[0].kwargs
            assert call_kwargs["task_id"] == "fake_task_id"
            assert call_kwargs["queue"] == "metadata_repository"
            assert call_kwargs["kwargs"]["action"] == "metadata_delegation"
        finally:
            # Restore original functions
            metadata_delegation.__globals__["bootstrap_state"] = (
                orig_bootstrap_state
            )
            metadata_delegation.__globals__["get_task_id"] = orig_get_task_id
            metadata_delegation.__globals__["repository_metadata"] = (
                orig_repository_metadata
            )
