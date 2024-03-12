# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
from datetime import datetime, timezone
from typing import Dict, List, Literal

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from repository_service_tuf_api import (
    bootstrap_state,
    get_task_id,
    repository_metadata,
    settings_repository,
)
from repository_service_tuf_api.common_models import Roles, TUFMetadata

with open("tests/data_examples/metadata/update-root-payload.json") as f:
    content = f.read()
update_payload_example = json.loads(content)

with open("tests/data_examples/bootstrap/das-payload.json") as f:
    content = f.read()
das_payload_example = json.loads(content)


class MetadataPostPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": update_payload_example}
    )

    metadata: Dict[Literal[Roles.ROOT.value], TUFMetadata]


class ResponseData(BaseModel):
    task_id: str | None = None
    last_update: datetime


class MetadataPostResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "task_id": "7a634b556f784ae88785d36425f9a218",
                    "last_update": "2022-12-01T12:10:00.578086",
                }
            }
        }
    )
    data: ResponseData | None = None
    message: str


def post_metadata(payload: MetadataPostPayload) -> MetadataPostResponse:
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False:
        raise HTTPException(
            status.HTTP_200_OK,
            detail={
                "message": "Task not accepted.",
                "error": (
                    f"Requires bootstrap finished. State: {bs_state.state}"
                ),
            },
        )

    task_id = get_task_id()

    repository_metadata.apply_async(
        kwargs={
            "action": "metadata_update",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    message = "Metadata update accepted."
    data = {
        "task_id": task_id,
        "last_update": datetime.now(timezone.utc),
    }
    return MetadataPostResponse(data=data, message=message)


class MetadataOnlinePostPayload(BaseModel):
    roles: List[Roles.online_roles_values()]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"roles": ["targets", "snapshot"]}
        }
    )


class MetadataOnlinePostResponse(BaseModel):
    data: Optional[ResponseData]
    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "task_id": "7a634b556f784ae88785d36425f9a218",
                    "last_update": "2022-12-01T12:10:00.578086",
                },
                "message": "Force new online metadata accepted.",
            }
        }
    )


def post_metadata_online(
    payload: MetadataOnlinePostPayload
) -> MetadataOnlinePostResponse:
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False:
        raise HTTPException(
            status.HTTP_200_OK,
            detail={
                "message": "Task not accepted.",
                "error": (
                    f"Requires bootstrap finished. State: {bs_state.state}"
                ),
            },
        )

    settings_repository.reload()
    if not settings_repository.get_fresh("TARGETS_ONLINE_KEY"):
        raise HTTPException(
            status.HTTP_200_OK,
            detail={
                "message": "Task not accepted.",
                "error": (
                    "Targets is an offline role - use other endpoint to update"
                ),
            },
        )

    # If no roles are provided, then bump all.
    if len(payload.roles) == 0:
        payload.roles = Roles.online_roles_values()

    task_id = get_task_id()
    repository_metadata.apply_async(
        kwargs={
            "action": "force_online_metadata_update",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    message = "Force online metadata update accepted."
    data = {
        "task_id": task_id,
        "last_update": datetime.now(),
    }
    return MetadataOnlinePostResponse(data=data, message=message)


class RolesData(BaseModel):
    root: TUFMetadata
    trusted_root: TUFMetadata | None = None


class SigningData(BaseModel):
    metadata: RolesData


class MetadataSignGetResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metadata": {"root": das_payload_example["metadata"]["root"]}
            }
        }
    )
    data: SigningData | None = None
    message: str


def get_metadata_sign() -> MetadataSignGetResponse:
    bs_state = bootstrap_state()
    # Adds support only when bootstrap is signing state
    if bs_state.bootstrap is False and bs_state.state != "signing":
        raise HTTPException(
            status.HTTP_200_OK,
            detail={
                "message": "No metadata pending signing available",
                "error": (
                    f"Requires bootstrap started. State: {bs_state.state}"
                ),
            },
        )

    settings_repository.reload()
    pending_signing = list(
        filter(lambda var: "SIGNING" in var, dir(settings_repository))
    )

    md_response = {}
    for role_setting in pending_signing:
        signing_role_obj = settings_repository.get(role_setting)
        if signing_role_obj is not None:
            signing_role_dict = signing_role_obj.to_dict()
            role = role_setting.split("_")[0].lower()
            md_response[role] = signing_role_dict

            trusted_obj = settings_repository.get(f"TRUSTED_{role.upper()}")
            if trusted_obj is not None:
                md_response[f"trusted_{role}"] = trusted_obj.to_dict()

    if len(md_response) > 0:
        data = {"metadata": md_response}
        msg = "Metadata role(s) pending signing"
    else:
        data = None
        msg = "No metadata pending signing available"

    return MetadataSignGetResponse(data=data, message=msg)


class MetadataSignPostResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "task_id": "7a634b556f784ae88785d36425f9a218",
                    "last_update": "2022-12-01T12:10:00.578086",
                }
            }
        }
    )
    data: ResponseData | None = None
    message: str


class MetadataSignature(BaseModel):
    keyid: str
    sig: str


class MetadataSignPostPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "root",
                "signature": {
                    "keyid": (
                        "800dfb5a1982b82b7893e58035e19f414f553fc08cbb1130cfbae"
                        "302a7b7fee5"
                    ),
                    "sig": (
                        "1e60e79c909affba4f8051c7b86c861048450b4b32f1b9c106c50"
                        "203a88877650a897b0c188af0ac0a530f1bccdafbdc2f92d0ee85"
                        "1864a6f24ddea031ef6b02"
                    ),
                },
            }
        }
    )
    role: str
    signature: MetadataSignature


def post_metadata_sign(
    payload: MetadataSignPostPayload,
) -> MetadataSignPostResponse:
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False and bs_state.state != "signing":
        raise HTTPException(
            status.HTTP_200_OK,
            detail={
                "message": "No signing pending.",
                "error": (
                    "Requires bootstrap in signing state. "
                    f"State: {bs_state.state}"
                ),
            },
        )

    task_id = get_task_id()

    repository_metadata.apply_async(
        kwargs={
            "action": "sign_metadata",
            "payload": payload.model_dump(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    message = "Metadata sign accepted."
    data = {
        "task_id": task_id,
        "last_update": datetime.now(timezone.utc),
    }

    return MetadataPostResponse(data=data, message=message)


class MetadataSignDeletePayload(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"role": "root"}})
    role: str


class MetadataSignDeleteResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "task_id": "7a634b556f784ae88785d36425f9a218",
                    "last_update": "2022-12-01T12:10:00.578086",
                },
                "message": "Metadata delete sign accepted.",
            }
        }
    )
    data: ResponseData | None = None
    message: str


def delete_metadata_sign(payload: MetadataSignDeletePayload):
    role = payload.role
    settings_repository.reload()
    signing_status = settings_repository.get_fresh(f"{role.upper()}_SIGNING")
    if signing_status is None:
        raise HTTPException(
            status.HTTP_200_OK,
            detail={
                "message": f"No signing process for {role}.",
                "error": f"The {role} role is not in a signing process.",
            },
        )

    task_id = get_task_id()
    repository_metadata.apply_async(
        kwargs={
            "action": "delete_sign_metadata",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    message = "Metadata sign delete accepted."
    data = {
        "task_id": task_id,
        "last_update": datetime.now(timezone.utc),
    }

    return MetadataSignDeleteResponse(data=data, message=message)
