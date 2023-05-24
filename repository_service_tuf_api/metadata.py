# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
from typing import Dict, Literal, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

from repository_service_tuf_api import (
    bootstrap_state,
    get_task_id,
    repository_metadata,
    settings_repository,
)
from repository_service_tuf_api.common_models import Roles, TUFMetadata


class MetadataPostPayload(BaseModel):
    metadata: Dict[Literal[Roles.ROOT.value], TUFMetadata]

    class Config:
        with open(
            "tests/data_examples/metadata/update-root-payload.json"
        ) as f:
            content = f.read()
        example = json.loads(content)
        schema_extra = {"example": example}


class PostData(BaseModel):
    task_id: Optional[str]


class MetadataPostResponse(BaseModel):
    data: Optional[PostData]
    message: str

    class Config:
        example = {
            "data": {
                "task_id": "7a634b556f784ae88785d36425f9a218",
            },
            "message": "Metadata Update accepted.",
        }

        schema_extra = {"example": example}


def post_metadata(payload: MetadataPostPayload) -> MetadataPostResponse:
    bs_state = bootstrap_state()
    if bs_state.bootstrap is False:
        raise HTTPException(
            status.HTTP_200_OK,
            detail={
                "message": "Task not accepted.",
                "error": (
                    f"It requires bootstrap finished. State: {bs_state.state}"
                ),
            },
        )

    task_id = get_task_id()

    repository_metadata.apply_async(
        kwargs={
            "action": "metadata_rotation",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    return MetadataPostResponse(
        data={"task_id": task_id}, message="Metadata update accepted."
    )


class GetData(BaseModel):
    metadata: Dict[Roles, TUFMetadata]


class MetadataSignGetResponse(BaseModel):
    data: Optional[GetData]
    message: str

    class Config:
        with open("tests/data_examples/bootstrap/payload.json") as f:
            content = f.read()
        example = json.loads(content)
        schema_extra = {
            "example": {"metadata": {"root": example["metadata"]["root"]}}
        }


def get_metadata_sign() -> MetadataSignGetResponse:
    bs_state = bootstrap_state()
    # Adds support only when bootstrap is signing state
    if bs_state.bootstrap is False and bs_state.state != "signing":
        raise HTTPException(
            status.HTTP_200_OK,
            detail={
                "message": "No signing available",
                "error": (
                    f"It requires bootstrap started. State: {bs_state.state}"
                ),
            },
        )

    settings_repository.reload()
    available_signing = list(
        filter(lambda var: "SIGNING" in var, dir(settings_repository))
    )

    metadata_response: Dict[str, TUFMetadata] = {}
    for singing in available_signing:
        signing_md = settings_repository.get(singing)
        if signing_md is not None:
            metadata_response[
                singing.split("_")[0].lower()
            ] = signing_md.to_dict()

    return MetadataSignGetResponse(
        data={"metadata": metadata_response},
        message="Available signing Metadata(s)",
    )


class MetadataSignPostResponse(BaseModel):
    data: Optional[PostData]
    message: str

    class Config:
        example = {
            "data": {
                "task_id": "7a634b556f784ae88785d36425f9a218",
            },
            "message": "Metadata Update accepted.",
        }

        schema_extra = {"example": example}


class MetadataSignature(BaseModel):
    keyid: str
    sig: str


class MetadataSignPostPayload(BaseModel):
    role: str
    signature: MetadataSignature

    class Config:
        schema_extra = {
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
                    "It requires bootstrap in signing state. "
                    f"State: {bs_state.state}"
                ),
            },
        )

    task_id = get_task_id()

    repository_metadata.apply_async(
        kwargs={
            "action": "sign_metadata",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    return MetadataPostResponse(
        data={"task_id": task_id}, message="Metadata sign accepted."
    )
