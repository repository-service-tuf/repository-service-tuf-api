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


class TestDelegationNestedBins:
    """Nested hash bins and their role-specific online key."""

    ONLINE_KEYID = (
        "cb20fa1061dde8e6267e0bef0981766aaadae168e917030f7f26edc7a0bab9c2"
    )

    def _payload(self, role_overrides=None, keys=None):
        payload = {
            "delegations": {
                "keys": keys
                if keys is not None
                else {
                    self.ONLINE_KEYID: {
                        "keytype": "ed25519",
                        "scheme": "ed25519",
                        "keyval": {"public": "4f66dabe"},
                        "x-rstuf-key-name": "fastapi-key",
                        "x-rstuf-online-key-uri": f"fn:{self.ONLINE_KEYID}",
                    }
                },
                "roles": [
                    {
                        "name": "fastapi",
                        "terminating": False,
                        "keyids": [],
                        "threshold": 1,
                        "x-rstuf-expire-policy": 365,
                        "x-rstuf-num-bins": 16,
                        "x-rstuf-role-online-key": self.ONLINE_KEYID,
                        "paths": ["fastapi/*"],
                    }
                ],
            }
        }
        if role_overrides:
            role = payload["delegations"]["roles"][0]
            for field, value in role_overrides.items():
                if value is None:
                    role.pop(field, None)
                else:
                    role[field] = value
        return payload

    def _mock_accepted(self, monkeypatch, fake_datetime):
        monkeypatch.setattr(
            f"{MOCK_PATH}.bootstrap_state",
            pretend.call_recorder(
                lambda: BootstrapState(bootstrap=True, state="FINISHED")
            ),
        )
        monkeypatch.setattr(
            f"{MOCK_PATH}.get_task_id",
            pretend.call_recorder(lambda: "fake_task_id"),
        )
        mock_apply_async = pretend.call_recorder(lambda **kw: None)
        monkeypatch.setattr(
            f"{MOCK_PATH}.repository_metadata",
            pretend.stub(apply_async=mock_apply_async),
        )
        monkeypatch.setattr(f"{MOCK_PATH}.datetime", fake_datetime)
        return mock_apply_async

    def test_post_forwards_nested_bins_fields(
        self, test_client, monkeypatch, fake_datetime
    ):
        """The Worker needs both extension fields, so they must survive."""
        mock_apply_async = self._mock_accepted(monkeypatch, fake_datetime)

        response = test_client.post(DELEGATIONS_URL, json=self._payload())

        assert response.status_code == status.HTTP_202_ACCEPTED
        role = mock_apply_async.calls[0].kwargs["kwargs"]["payload"][
            "delegations"
        ]["roles"][0]
        assert role["x-rstuf-num-bins"] == 16
        assert role["x-rstuf-role-online-key"] == self.ONLINE_KEYID

    def test_post_rejects_num_bins_not_power_of_two(
        self, test_client, monkeypatch, fake_datetime
    ):
        self._mock_accepted(monkeypatch, fake_datetime)

        response = test_client.post(
            DELEGATIONS_URL, json=self._payload({"x-rstuf-num-bins": 15})
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "power of 2" in response.text

    def test_post_rejects_nested_bins_threshold_above_one(
        self, test_client, monkeypatch, fake_datetime
    ):
        self._mock_accepted(monkeypatch, fake_datetime)

        response = test_client.post(
            DELEGATIONS_URL, json=self._payload({"threshold": 2})
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "threshold 1" in response.text

    def test_post_rejects_role_online_key_without_bins(
        self, test_client, monkeypatch, fake_datetime
    ):
        self._mock_accepted(monkeypatch, fake_datetime)

        response = test_client.post(
            DELEGATIONS_URL, json=self._payload({"x-rstuf-num-bins": None})
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "without x-rstuf-num-bins" in response.text

    def test_post_rejects_role_online_key_signing_its_own_role(
        self, test_client, monkeypatch, fake_datetime
    ):
        """A delegation cannot sign itself with its bins' online key."""
        self._mock_accepted(monkeypatch, fake_datetime)

        response = test_client.post(
            DELEGATIONS_URL,
            json=self._payload({"keyids": [self.ONLINE_KEYID]}),
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "cannot sign itself" in response.text

    def test_post_rejects_undeclared_role_online_key(
        self, test_client, monkeypatch, fake_datetime
    ):
        self._mock_accepted(monkeypatch, fake_datetime)

        response = test_client.post(
            DELEGATIONS_URL,
            json=self._payload({"x-rstuf-role-online-key": "unknown"}),
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "not declared in delegations.keys" in response.text

    def test_post_rejects_role_online_key_without_uri(
        self, test_client, monkeypatch, fake_datetime
    ):
        """Without a signer URI the Worker cannot sign the bins."""
        self._mock_accepted(monkeypatch, fake_datetime)

        payload = self._payload(
            keys={
                self.ONLINE_KEYID: {
                    "keytype": "ed25519",
                    "scheme": "ed25519",
                    "keyval": {"public": "4f66dabe"},
                    "x-rstuf-key-name": "fastapi-key",
                }
            }
        )
        response = test_client.post(DELEGATIONS_URL, json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "x-rstuf-online-key-uri" in response.text

    def test_post_rejects_unsupported_online_key_uri_scheme(
        self, test_client, monkeypatch, fake_datetime
    ):
        """The scheme selects the signer backend, so it is allowlisted."""
        self._mock_accepted(monkeypatch, fake_datetime)

        payload = self._payload(
            keys={
                self.ONLINE_KEYID: {
                    "keytype": "ed25519",
                    "scheme": "ed25519",
                    "keyval": {"public": "4f66dabe"},
                    "x-rstuf-online-key-uri": "ssh://attacker/key",
                }
            }
        )
        response = test_client.post(DELEGATIONS_URL, json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "unsupported URI scheme" in response.text

    def test_post_rejects_duplicate_role_names(
        self, test_client, monkeypatch, fake_datetime
    ):
        self._mock_accepted(monkeypatch, fake_datetime)

        payload = self._payload()
        payload["delegations"]["roles"].append(
            dict(payload["delegations"]["roles"][0])
        )
        response = test_client.post(DELEGATIONS_URL, json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "duplicate role names" in response.text

    def test_put_forwards_nested_bins_fields(
        self, test_client, monkeypatch, fake_datetime
    ):
        """The update path uses the same model, so it validates identically."""
        mock_apply_async = self._mock_accepted(monkeypatch, fake_datetime)

        response = test_client.put(DELEGATIONS_URL, json=self._payload())

        assert response.status_code == status.HTTP_202_ACCEPTED
        payload = mock_apply_async.calls[0].kwargs["kwargs"]["payload"]
        assert payload["action"] == "update"
        role = payload["delegations"]["roles"][0]
        assert role["x-rstuf-num-bins"] == 16
        assert role["x-rstuf-role-online-key"] == self.ONLINE_KEYID
