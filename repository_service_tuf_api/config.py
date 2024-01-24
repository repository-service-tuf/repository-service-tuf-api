# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict

from repository_service_tuf_api import (
    bootstrap_state,
    get_task_id,
    repository_metadata,
    settings_repository,
)
from repository_service_tuf_api.common_models import Roles


class PutData(BaseModel):
    task_id: str
    last_update: datetime


class PutResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "task_id": "06ee6db3cbab4b26be505352c2f2e2c3",
                    "last_update": "2022-12-01T12:10:00.578086",
                },
                "message": "Settings successfully submitted.",
            }
        }
    )

    data: PutData | None = None
    message: str


class Settings(BaseModel):
    # Only online roles can be dict keys
    expiration: Dict[Roles.online_roles_values(), int]


with open("tests/data_examples/config/update_settings.json") as f:
    content = f.read()
put_payload = json.loads(content)


class PutPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": put_payload,
        }
    )

    settings: Settings


def put(payload: PutPayload):
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={
                "message": "No Repository Settings/Config found.",
                "error": f"It requires bootstrap. State: {bs_state.state}",
            },
        )

    task_id = get_task_id()

    repository_metadata.apply_async(
        kwargs={
            "action": "update_settings",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    data = {
        "task_id": task_id,
        "last_update": datetime.now(timezone.utc),
    }

    return PutResponse(data=data, message="Settings successfully submitted.")


with open("tests/data_examples/config/settings.json") as f:
    content = f.read()
example_settings = json.loads(content)


class GetResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": example_settings,
                "message": "Current Settings",
            }
        }
    )
    data: Dict[str, Any]
    message: str


def get() -> GetResponse:
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={
                "message": "No Repository Settings/Config found.",
                "error": f"It requires bootstrap. State: {bs_state.state}",
            },
        )

    # Forces all values to be refreshed
    settings_repository.fresh()
    lower_case_settings = {}
    for k, v in settings_repository.to_dict().items():
        if isinstance(v, str):
            v = v.lower()

        if v == "none":
            continue

        lower_case_settings[k.lower()] = v

    current_settings = {**lower_case_settings}

    return GetResponse(data=current_settings, message="Current Settings")
