import glob
import json
from typing import Dict, List, Literal, Optional

from fastapi import HTTPException, status

from kaprien_api import keyvault, storage, tuf, tuf_repository
from kaprien_api.utils import (
    BaseErrorResponse,
    BaseModel,
    TUFMetadata,
    save_settings,
)


class SettingsKeyBody(BaseModel):
    keytype: str
    scheme: str
    keyid: str
    keyid_hash_algorithms: List[str]
    keyval: Dict[Literal["public", "private"], str]


class SettingsKeys(BaseModel):
    filename: str
    password: str
    key: SettingsKeyBody


class RoleSettings(BaseModel):
    # This is the from kaprien-cli RolesKeysInput
    expiration: int
    num_of_keys: int
    threshold: int
    keys: Optional[Dict[str, SettingsKeys]]
    offline_keys: bool
    paths: Optional[List[str]] = None
    number_hash_prefixes: Optional[int] = None


class ServiceSettings(BaseModel):
    targets_base_url: str


class Settings(BaseModel):
    roles: Dict[
        Literal[
            tuf.Roles.ROOT.value,
            tuf.Roles.TARGETS.value,
            tuf.Roles.SNAPSHOT.value,
            tuf.Roles.TIMESTAMP.value,
            tuf.Roles.BIN.value,
            tuf.Roles.BINS.value,
        ],
        RoleSettings,
    ]
    service: ServiceSettings


class BootstrapPayload(BaseModel):
    settings: Settings
    metadata: Dict[str, TUFMetadata]

    class Config:
        with open("tests/data_examples/bootstrap/payload.json") as f:
            content = f.read()
        example = json.loads(content)
        schema_extra = {"example": example}


class BootstrapResponse(BaseModel):
    data: Optional[Dict[str, TUFMetadata]]
    bootstrap: Optional[bool]
    message: Optional[str]

    class Config:
        metadata_files = glob.glob("tests/data_examples/metadata/*.json")
        metadata: dict = dict()
        for metadata_file in metadata_files:
            with open(metadata_file) as f:
                content = f.read()
                example_metadata = json.loads(content)
            filename = metadata_file.split("/")[-1].replace(".json", "")
            metadata[filename] = example_metadata

        schema_extra = {"example": metadata}


def get_bootstrap():
    response = BootstrapResponse()

    if tuf_repository.is_initialized is True:
        response.bootstrap = True
        response.message = "System already has a Metadata."
    else:
        response.bootstrap = False
        response.message = "System available for bootstrap."

    return response


def post_bootstrap(payload):
    if tuf_repository.is_initialized:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail=BaseErrorResponse(
                error="System already has a Metadata."
            ).dict(exclude_none=True),
        )

    # Store online keys to the KeyVault Service and configuration
    for rolename, settings in payload.settings.roles.items():
        save_settings(f"{rolename.upper()}_EXPIRATION", settings.expiration)

        # online keys
        if settings.offline_keys is False:
            keyvault.put(rolename, settings.dict().get("keys").values())

    save_settings(
        "TARGETS_BASE_URL", payload.settings.service.targets_base_url
    )

    for rolename, data in payload.metadata.items():
        metadata = tuf.Metadata.from_dict(
            data.dict(by_alias=True, exclude_none=True)
        )
        if "." not in rolename and rolename != tuf.Roles.TIMESTAMP.value:
            filename = f"1.{rolename}.json"
        else:
            filename = f"{rolename}.json"

        metadata.to_file(filename, storage_backend=storage)
