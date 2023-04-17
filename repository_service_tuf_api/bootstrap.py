# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import json
import logging
from typing import Dict, Literal, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from repository_service_tuf_api import (
    get_task_id,
    is_bootstrap_done,
    repository_metadata,
    settings_repository,
)
from repository_service_tuf_api.common_models import (
    BaseErrorResponse,
    Roles,
    TUFMetadata,
)
from repository_service_tuf_api.config import save_settings


class ServiceSettings(BaseModel):
    targets_base_url: str
    number_of_delegated_bins: int = Field(gt=1, lt=16385)
    targets_online_key: bool


class Settings(BaseModel):
    expiration: Dict[Roles.values(), int]
    services: ServiceSettings


class BootstrapPayload(BaseModel):
    settings: Settings
    metadata: Dict[Literal[Roles.ROOT.value], TUFMetadata]

    class Config:
        with open("tests/data_examples/bootstrap/payload.json") as f:
            content = f.read()
        example = json.loads(content)
        schema_extra = {"example": example}


class PostData(BaseModel):
    task_id: Optional[str]


class BootstrapPostResponse(BaseModel):
    data: Optional[PostData]
    message: str

    class Config:
        example = {
            "data": {
                "task_id": "7a634b556f784ae88785d36425f9a218",
            },
            "message": "Bootstrap accepted.",
        }

        schema_extra = {"example": example}


class GetData(BaseModel):
    bootstrap: bool


class BootstrapGetResponse(BaseModel):
    data: Optional[GetData]
    message: str

    class Config:
        example = {
            "data": {"bootstrap": False},
            "message": "System available for bootstrap.",
        }

        schema_extra = {"example": example}


def get_bootstrap():
    if is_bootstrap_done() is True:
        response = BootstrapGetResponse(
            data={"bootstrap": True}, message="System LOCKED for bootstrap."
        )
    else:
        response = BootstrapGetResponse(
            data={"bootstrap": False},
            message="System available for bootstrap.",
        )
    return response


def post_bootstrap(payload: BootstrapPayload) -> BootstrapPostResponse:
    if is_bootstrap_done() is True:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail=BaseErrorResponse(
                error="System already has a Metadata."
            ).dict(exclude_none=True),
        )

    # Store settings
    logging.debug("Saving settings")
    for role in Roles:
        rolename = role.value.upper()
        threshold = 1
        num_of_keys = 1
        if rolename == Roles.ROOT.value.upper():
            md = payload.metadata
            # The key to the root role is the name of the root file which uses
            # consistent snapshot or in the format: <VERSION_NUMBER>.root.json
            root_file_name = [name for name in md if name.endswith("root")][0]
            threshold = md[root_file_name].signed.roles[role.value].threshold
            num_of_keys = len(md[root_file_name].signatures)

        save_settings(
            f"{rolename}_EXPIRATION",
            payload.settings.expiration[role.value],
            settings_repository,
        )
        save_settings(f"{rolename}_THRESHOLD", threshold, settings_repository)
        save_settings(f"{rolename}_NUM_KEYS", num_of_keys, settings_repository)

    save_settings(
        "NUMBER_OF_DELEGATED_BINS",
        payload.settings.services.number_of_delegated_bins,
        settings_repository,
    )

    save_settings(
        "TARGETS_BASE_URL",
        payload.settings.services.targets_base_url,
        settings_repository,
    )

    save_settings(
        "TARGETS_ONLINE_KEY",
        payload.settings.services.targets_online_key,
        settings_repository,
    )

    task_id = get_task_id()
    settings_repository.BOOTSTRAP = task_id
    save_settings("BOOTSTRAP", task_id, settings_repository)
    logging.debug(f"Bootstrap locked with id {task_id}")

    logging.debug(f"Bootstrap task {task_id} sent")
    repository_metadata.apply_async(
        kwargs={
            "action": "bootstrap",
            "payload": payload.dict(by_alias=True, exclude_none=True),
        },
        task_id=task_id,
        queue="metadata_repository",
        acks_late=True,
    )

    return BootstrapPostResponse(
        data={"task_id": task_id}, message="Bootstrap accepted."
    )
