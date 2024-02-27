# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
import logging
import re
import time
from datetime import datetime
from threading import Thread
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from repository_service_tuf_api import (
    bootstrap_state,
    get_task_id,
    pre_lock_bootstrap,
    release_bootstrap_lock,
    repository_metadata,
)
from repository_service_tuf_api.common_models import (
    BaseErrorResponse,
    TUFMetadata,
)

# Pattern of allowed names to be used by custom target delegated roles
DELEGATED_NAMES_PATTERN = "[a-zA-Z0-9_-]+"


with open("tests/data_examples/bootstrap/payload_bins.json") as f:
    content = f.read()
payload_example = json.loads(content)


class Role(BaseModel):
    expiration: int = Field(gt=0)


class BinsRole(Role):
    number_of_delegated_bins: int = Field(gt=1, lt=16385)


class DelegatedRole(Role):
    # Note: No validation is required for path_patterns as these patterns are
    # only used to distribute artifacts. No files are created based on them.
    path_patterns: List[str] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def validate_path_patterns(cls, values: Dict[str, Any]):
        path_patterns = values.get("path_patterns")
        if any(len(pattern) < 1 for pattern in path_patterns):
            raise ValueError("No empty strings are allowed as path patterns")

        return values


class RolesData(BaseModel):
    root: Role
    targets: Role
    snapshot: Role
    timestamp: Role
    bins: Optional[BinsRole] = Field(default=None)
    delegated_roles: Optional[Dict[str, DelegatedRole]] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def validate_delegations(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        bins = values.get("bins")
        delegated_roles = values.get("delegated_roles")
        if (bins is None and delegated_roles is None) or (
            bins is not None and delegated_roles is not None
        ):
            err_msg = "Exactly one of 'bins' and 'delegated_roles' must be set"
            raise ValueError(err_msg)

        return values

    @model_validator(mode="before")
    @classmethod
    def validate_delegated_roles_names(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Validation of custom target delegated names is required as otherwise
        # an attacker can use a custom target name to point to a specific place
        # in a file system and override a file or cause unexpected behavior.
        delegated_roles = values.get("delegated_roles")
        if delegated_roles is not None:
            # The keys of the delegated_roles dict are the names of the roles.
            for role_name in delegated_roles.keys():
                if re.fullmatch(DELEGATED_NAMES_PATTERN, role_name) is None:
                    raise ValueError(
                        f"Delegated custom target name {role_name} not allowed"
                        " Only a-z, A-Z, 0-9, - and _ characters can be used"
                    )

        return values


class Settings(BaseModel):
    roles: RolesData


class BootstrapPayload(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": payload_example})
    settings: Settings
    metadata: Dict[str, TUFMetadata]
    timeout: int | None = Field(default=300, description="Timeout in seconds")


class PostData(BaseModel):
    task_id: str | None = None
    last_update: datetime


class BootstrapPostResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "task_id": "7a634b556f784ae88785d36425f9a218",
                    "last_update": "2022-12-01T12:10:00.578086",
                },
                "message": "Bootstrap accepted.",
            }
        }
    )
    data: PostData | None = None
    message: str


class GetData(BaseModel):
    bootstrap: bool
    state: str | None = None
    id: str | None = None


class BootstrapGetResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {"bootstrap": False},
                "message": "System available for bootstrap.",
            }
        }
    )
    data: GetData | None = None
    message: str


def _check_bootstrap_status(task_id, timeout):
    time_timeout = time.time() + timeout

    while True:
        task = repository_metadata.AsyncResult(task_id)
        if task.status == "SUCCESS":
            return
        elif task.status == "FAILURE":
            release_bootstrap_lock()
            return
        else:
            if time.time() > time_timeout:
                task.revoke(terminate=True)
                release_bootstrap_lock()
                return

            continue


def get_bootstrap() -> BootstrapGetResponse:
    bs_state = bootstrap_state()
    # If bootstrap ceremony has completed, is executed in the moment ("pre")
    # or is in the process of DAS signing ("signing") we consider it as locked.
    if bs_state.bootstrap is True or bs_state.state in ["pre", "signing"]:
        message = "System LOCKED for bootstrap."

    else:
        message = "System available for bootstrap."

    response = BootstrapGetResponse(
        data={
            "bootstrap": bs_state.bootstrap,
            "state": bs_state.state,
            "id": bs_state.task_id,
        },
        message=message,
    )

    return response


def post_bootstrap(payload: BootstrapPayload) -> BootstrapPostResponse:
    bs_state = bootstrap_state()
    # If bootstrap ceremony has completed, is executed in the moment ("pre")
    # or is in the process of DAS signing ("signing") we consider it as locked.
    if bs_state.bootstrap is True or bs_state.state in ["pre", "signing"]:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail=BaseErrorResponse(
                error=(
                    "System already has a Metadata. "
                    f"State: {bs_state.state}"
                )
            ).dict(exclude_none=True),
        )

    task_id = get_task_id()
    pre_lock_bootstrap(task_id)
    repository_metadata.apply_async(
        kwargs={
            "action": "bootstrap",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )
    logging.info(f"Bootstrap task {task_id} sent")

    # start a thread to check the bootstrap process
    logging.info(f"Bootstrap process timeout: {payload.timeout} seconds")
    Thread(
        None,
        _check_bootstrap_status,
        kwargs={
            "task_id": task_id,
            "timeout": payload.timeout,
        },
    ).start()

    data = {
        "task_id": task_id,
        "last_update": datetime.now(),
    }

    return BootstrapPostResponse(
        data=data,
        message="Bootstrap accepted.",
    )
