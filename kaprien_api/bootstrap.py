import glob
import json
from typing import Dict, List, Literal, Optional

from fastapi import HTTPException, status

from kaprien_api import keyvault, storage, tuf, tuf_repository
from kaprien_api.utils import BaseErrorResponse, BaseModel, save_settings


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


class Settings(BaseModel):
    # This is the from kaprien-cli RolesKeysInput
    expiration: int
    num_of_keys: int
    threshold: int
    keys: Optional[Dict[str, SettingsKeys]]
    offline_keys: bool
    paths: Optional[List[str]] = None
    number_hash_prefixes: Optional[int] = None


class TUFSignedDelegationsRoles(BaseModel):
    name: str
    terminating: bool
    keyids: List[str]
    threshold: int
    paths: Optional[List[str]]
    path_hash_prefixes: Optional[List[str]]


class TUFKeys(BaseModel):
    keytype: str
    scheme: str
    keyval: Dict[Literal["public", "private"], str]


class TUFSignedDelegations(BaseModel):
    keys: Dict[str, TUFKeys]
    roles: List[TUFSignedDelegationsRoles]


class TUFSignedMetaFile(BaseModel):
    version: int


class TUFSignedRoles(BaseModel):
    keyids: List[str]
    threshold: int


class TUFSigned(BaseModel):
    type: str
    version: int
    spec_version: str
    expires: str
    keys: Optional[Dict[str, TUFKeys]]
    roles: Optional[
        Dict[
            Literal[
                tuf.Roles.ROOT.value,
                tuf.Roles.TARGETS.value,
                tuf.Roles.SNAPSHOT.value,
                tuf.Roles.TIMESTAMP.value,
                tuf.Roles.BIN.value,
                tuf.Roles.BINS.value,
            ],
            TUFSignedRoles,
        ]
    ]
    meta: Optional[Dict[str, TUFSignedMetaFile]]
    targets: Optional[Dict[str, str]]
    delegations: Optional[TUFSignedDelegations]

    class Config:
        fields = {"type": "_type"}


class TUFSignatures(BaseModel):
    keyid: str
    sig: str


class TUFMetadata(BaseModel):
    signatures: List[TUFSignatures]
    signed: TUFSigned


class BootstrapPayload(BaseModel):
    settings: Dict[
        Literal[
            tuf.Roles.ROOT.value,
            tuf.Roles.TARGETS.value,
            tuf.Roles.SNAPSHOT.value,
            tuf.Roles.TIMESTAMP.value,
            tuf.Roles.BIN.value,
            tuf.Roles.BINS.value,
        ],
        Settings,
    ]
    metadata: Dict[str, TUFMetadata]

    class Config:
        with open("tests/data_examples/bootstrap/payload.json") as f:
            content = f.read()
        example = json.loads(content)
        schema_extra = {"example": example}


class BootstrapResponse(BaseModel):
    data: Optional[TUFMetadata]
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
    # Store online keys to the KeyVault Service and configuration
    if tuf_repository.is_initialized:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail=BaseErrorResponse(
                error="System already has a Metadata."
            ).dict(exclude_none=True),
        )

    for rolename, settings in payload.settings.items():
        save_settings(f"{rolename.upper()}_EXPIRATION", settings.expiration)

        # online keys
        if settings.offline_keys is False:
            keyvault.put(rolename, settings.dict().get("keys").values())

    for rolename, data in payload.metadata.items():
        metadata = tuf.Metadata.from_dict(
            data.dict(by_alias=True, exclude_none=True)
        )
        if "." not in rolename:
            filename = f"1.{rolename}.json"
        elif rolename == tuf.Roles.TIMESTAMP.value:
            filename = rolename
        else:
            filename = f"{rolename}.json"

        metadata.to_file(filename, storage_backend=storage)
