# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
from typing import Any, Dict

from fastapi import HTTPException, status
from pydantic import BaseModel

from repository_service_tuf_api import is_bootstrap_done, settings_repository


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


def get():
    if is_bootstrap_done() is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Configuration available only after bootstrap process"
            },
        )

    settings_repository.reload()
    lower_case_settings = {}
    for k, v in settings_repository.to_dict().items():
        if isinstance(v, str):
            v = v.lower()

        if v == "none":
            continue

        lower_case_settings[k.lower()] = v

    current_settings = {**lower_case_settings}

    return Response(data=current_settings, message="Current Settings")
