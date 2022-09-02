import json
from typing import Any, Dict

from dynaconf import Dynaconf, loaders
from dynaconf.base import DynaBox
from fastapi import HTTPException, status
from pydantic import BaseModel

from kaprien_api import settings_repository


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


def save_settings(key: str, value: Any, settings: Dynaconf):
    settings.store[key] = value
    settings_data = settings.as_dict(env=settings.current_env)
    loaders.write(
        settings.SETTINGS_FILE_FOR_DYNACONF[0],
        DynaBox(settings_data).to_dict(),
        env=settings.current_env,
    )


def is_bootstrap_done():
    if settings_repository.get("BOOTSTRAP"):
        return True
    else:
        return False


def get():
    if is_bootstrap_done() is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"error": "System has not a Repository Metadata"},
        )

    lower_case_settings = {}
    for k, v in settings_repository.to_dict().items():
        if isinstance(v, str):
            v = v.lower()

        if v == "none":
            continue

        lower_case_settings[k.lower()] = v

    current_settings = {**lower_case_settings}

    return Response(data=current_settings, message="Current Settings")
