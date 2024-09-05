# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict

from repository_service_tuf_api import (
    bootstrap_state,
    get_task_id,
    repository_metadata,
    settings_repository,
)
from repository_service_tuf_api.common_models import (
    Roles,
    TUFDelegations,
    TUFMetadata,
    TUFSignatures,
)

with open("tests/data_examples/metadata/update-root-payload.json") as f:
    content = f.read()
update_payload_example = json.loads(content)

with open("tests/data_examples/bootstrap/das-payload.json") as f:
    content = f.read()
das_payload_example = json.loads(content)

with open("tests/data_examples/metadata/delegation-payload.json") as f:
    content = f.read()
delegation_payload_example = json.loads(content)


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
            status.HTTP_404_NOT_FOUND,
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


class MetadataDelegationsPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": delegation_payload_example}
    )

    delegations: TUFDelegations


def metadata_delegation(payload: MetadataDelegationsPayload, action: str):
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
    worker_payload = payload.model_dump(by_alias=True, exclude_none=True)
    worker_payload["action"] = action

    repository_metadata.apply_async(
        kwargs={
            "action": "metadata_delegation",
            "payload": worker_payload,
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    message = "Metadata delegation accepted."
    data = {
        "task_id": task_id,
        "last_update": datetime.now(timezone.utc),
    }

    return MetadataPostResponse(data=data, message=message)


class MetadataOnlinePostPayload(BaseModel):
    roles: List[str]

    model_config = ConfigDict(
        json_schema_extra={"example": {"roles": ["targets", "snapshot"]}}
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
    payload: MetadataOnlinePostPayload,
) -> MetadataOnlinePostResponse:
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Task not accepted.",
                "error": (
                    f"Requires bootstrap finished. State: {bs_state.state}"
                ),
            },
        )

    roles = payload.roles
    targets_in = "targets" in roles
    settings_repository.reload()
    targets_online = settings_repository.get_fresh("TARGETS_ONLINE_KEY", True)
    if targets_in and not targets_online:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Task not accepted.",
                "error": (
                    "Targets is an offline role - use other endpoint to update"
                ),
            },
        )

    delegated_roles = settings_repository.get_fresh("DELEGATED_ROLES_NAMES")
    # All delegated roles names should start with "bins" if we are using
    # hash bin delegation and none of the delegated roles should start with
    # "bins" if we are using custom target delegation.
    bins_used = True if delegated_roles[0].startswith("bins") else False
    if bins_used:
        # This indicates succinct hash bins are used
        if len(roles) > 0 and any(not Roles.is_role(role) for role in roles):
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Task not accepted.",
                    "error": (
                        "Hash bin delegation is used and only "
                        f"{Roles.all_str()} roles can be bumped"
                    ),
                },
            )
    else:
        if Roles.BINS.value in roles:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Task not accepted.",
                    "error": (
                        "Custom target delegation used and "
                        "bins cannot be bumped"
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
    trusted_targets: TUFMetadata | None = None


class SigningData(BaseModel):
    metadata: RolesData | Any


class MetadataSignGetResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "metadata": {
                        "root": das_payload_example["metadata"]["root"]
                    }
                }
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
            status.HTTP_404_NOT_FOUND,
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
    trusted_root = settings_repository.get(f"TRUSTED_ROOT")
    trusted_targets = settings_repository.get(f"TRUSTED_TARGETS")

    if trusted_root:
        md_response["trusted_root"] = trusted_root.to_dict()
    else:
        md_response["trusted_root"] = None

    if trusted_targets:
        md_response["trusted_targets"] = trusted_targets.to_dict()
    else:
        md_response["trusted_targets"] = None

    for role_setting in pending_signing:
        signing_role_obj = settings_repository.get(role_setting)
        if signing_role_obj is not None:
            signing_role_dict = signing_role_obj.to_dict()
            role = role_setting.split("_")[0].lower()
            md_response[role] = signing_role_dict

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


class MetadataSignPostPayload(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "root",
                "signature": {
                    "keyid": (
                        "2f685fa7546f1856b123223ab086b3def14c89d24eef18f49c325"
                        "08c2f60e241"
                    ),
                    "sig": (
                        "7561c1db8a1f5e27de475f6b1f8f0d6fff7f53957784f689d86ca"
                        "b9a76de2adf48c5e2573e81b6f5bda6c4b9fb6611df985f08d7d2"
                        "7e22e31c73833ec130b505b3da02a78c6b730a3ebf21b4878f406"
                        "7ddbd153f8f498e5787f2e9fd29dd4564358795664b33572919fb"
                        "2f2a22f25182d83da4e5109d5067198bb85e20bff1385a06821e9"
                        "3362dfbfbc1e1820965c8e555c228c27b2c4c697936c2036b163b"
                        "2ce126c9dc936ed66c38cda504062bc88c017790ccb9c78fd6fcc"
                        "06f329cfaf17dc4e72343c9de17b12fc699f894868bbfff5b8437"
                        "939442dfd2887e0244038583ec6b9fd7f96247b6d45b3700c1b04"
                        "028e04779870afb473782be9e422551a371"
                    ),
                },
            }
        }
    )
    role: str
    signature: TUFSignatures


def post_metadata_sign(
    payload: MetadataSignPostPayload,
) -> MetadataSignPostResponse:
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False and bs_state.state != "signing":
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
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
            status.HTTP_404_NOT_FOUND,
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
