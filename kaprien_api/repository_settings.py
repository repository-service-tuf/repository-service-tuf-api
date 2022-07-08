import json
from typing import Dict, Optional

from fastapi import HTTPException, status

from kaprien_api import settings, tuf, tuf_repository
from kaprien_api.utils import BaseModel


class CurrentSettingsServiceBackendParams(BaseModel):
    required: bool
    current_value: str


class CurrentSettingsServiceBackend(BaseModel):
    using: str
    parameters: Optional[Dict[str, CurrentSettingsServiceBackendParams]]


class CurrentSettings(BaseModel):
    storage_backend: CurrentSettingsServiceBackend
    keyvault_backend: CurrentSettingsServiceBackend
    roles_expirations: Dict[str, int]


class Response(BaseModel):
    data: CurrentSettings
    message: str

    class Config:
        with open(
            "tests/data_examples/repository_settings/settings.json"
        ) as f:
            content = f.read()
        example_settings = json.loads(content)

        schema_extra = {
            "example": {
                "data": example_settings,
                "message": "Current Settings",
            }
        }


def get():
    if tuf_repository.is_initialized is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"error": "System has not a Repository Metadata"},
        )
    services_backend = {
        "storage_backend": {
            "using": settings.STORAGE_BACKEND.__name__,
            "parameters": {
                i.name: {
                    "required": i.required,
                    "current_value": settings.get(i.name),
                }
                for i in settings.STORAGE_BACKEND.settings()
            },
        },
        "keyvault_backend": {
            "using": settings.KEYVAULT_BACKEND.__name__,
            "parameters": {
                i.name: {
                    "required": i.required,
                    "current_value": settings.get(i.name),
                }
                for i in settings.KEYVAULT_BACKEND.settings()
            },
        },
    }
    roles_settings = {
        "roles_expirations": {
            role.value: settings.get(f"{role.value}_EXPIRATION")
            for role in tuf.Roles
        },
    }
    current_settings = {**services_backend, **roles_settings}

    return Response(data=current_settings, message="Current Settings")
