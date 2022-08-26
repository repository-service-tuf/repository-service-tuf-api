from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from dynaconf import Dynaconf, loaders
from dynaconf.utils.boxing import DynaBox
from pydantic import BaseModel, Field

from kaprien_api import settings_repository


class Roles(Enum):
    ROOT = "root"
    TARGETS = "targets"
    SNAPSHOT = "snapshot"
    TIMESTAMP = "timestamp"
    BIN = "bin"
    BINS = "bins"


class BaseErrorResponse(BaseModel):
    error: str = Field(description="Error message")
    details: Optional[Dict[str, str]] = Field(description="Error details")
    code: Optional[int] = Field(description="Error code if available")


class TUFSignedDelegationsRoles(BaseModel):
    name: str
    terminating: bool
    keyids: List[str]
    threshold: int
    paths: Optional[List[str]]
    path_hash_prefixes: Optional[List[str]]


class TUFSignedDelegationsSuccinctRoles(BaseModel):
    bit_length: int = Field(gt=0, lt=33)
    name_prefix: str
    keyids: List[str]
    threshold: int


class TUFKeys(BaseModel):
    keytype: str
    scheme: str
    keyval: Dict[Literal["public", "private"], str]


class TUFSignedDelegations(BaseModel):
    keys: Dict[str, TUFKeys]
    roles: Optional[List[TUFSignedDelegationsRoles]]
    succinct_roles: Optional[TUFSignedDelegationsSuccinctRoles]


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
                Roles.ROOT.value,
                Roles.TARGETS.value,
                Roles.SNAPSHOT.value,
                Roles.TIMESTAMP.value,
                Roles.BIN.value,
                Roles.BINS.value,
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


def get_task_id():
    return uuid4().hex
