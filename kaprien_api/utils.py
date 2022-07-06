from typing import Any, Dict, List, Literal, Optional

from dynaconf import loaders
from dynaconf.utils.boxing import DynaBox
from pydantic import BaseModel, Field

from kaprien_api import SETTINGS_FILE, settings, tuf


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


def save_settings(key: str, value: Any):
    settings.store[key] = value
    settings_data = settings.as_dict(env=settings.current_env)
    loaders.write(
        SETTINGS_FILE,
        DynaBox(settings_data).to_dict(),
        env=settings.current_env,
    )
