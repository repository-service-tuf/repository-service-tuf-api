# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException, status
from pydantic import BaseModel

from repository_service_tuf_api import (
    bootstrap_state,
    get_task_id,
    repository_metadata,
    settings_repository,
)
from repository_service_tuf_api.common_models import Roles


class Response(BaseModel):
    data: Dict[str, Any]
    message: str

    class Config:
        with open("tests/data_examples/config/settings.json") as f:
            content = f.read()
        example_settings = json.loads(content)

        schema_extra = {
            "example": {
                "data": example_settings,
                "message": "Current Settings",
            }
        }


class PutResponse(BaseModel):
    data: Dict[str, Any]
    message: str

    class Config:
        with open("tests/data_examples/config/update_settings.json") as f:
            content = f.read()
        example_settings = json.loads(content)

        example = {
            "data": {
                "task_id": "06ee6db3cbab4b26be505352c2f2e2c3",
                "last_update": "2022-12-01T12:10:00.578086",
            },
            "message": "Settings successfully submitted.",
        }

        schema_extra = {"example": example}


class Settings(BaseModel):
    # Only online roles can be dict keys
    expiration: Dict[Roles.online_roles_values(), int]


class PutPayload(BaseModel):
    settings: Settings

    class Config:
        with open("tests/data_examples/config/update_settings.json") as f:
            content = f.read()
        example_settings = json.loads(content)

        schema_extra = {
            "example": example_settings,
        }


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
        "last_update": datetime.now(),
    }
    message = "Settings successfully submitted."

    return PutResponse(data=data, message=message)


def get():
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

    return Response(data=current_settings, message="Current Settings")
