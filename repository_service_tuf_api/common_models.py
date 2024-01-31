# SPDX-FileCopyrightText: 2023 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Extra, Field, root_validator


class Roles(Enum):
    ROOT = "root"
    TARGETS = "targets"
    SNAPSHOT = "snapshot"
    TIMESTAMP = "timestamp"
    BINS = "bins"

    @staticmethod
    def values() -> List[str]:
        return Literal["root", "targets", "snapshot", "timestamp", "bins"]

    @staticmethod
    def online_roles_values() -> List[str]:
        return Literal["targets", "snapshot", "timestamp", "bins"]


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
    # We cannot add the limit range
    # https://github.com/tiangolo/fastapi/discussions/9140
    # bit_length: int = Field(gt=0, lt=15)
    bit_length: int
    name_prefix: str
    keyids: List[str]
    threshold: int


class TUFKeys(BaseModel):
    keytype: str
    scheme: str
    keyval: Dict[Literal["public", "private"], str]
    name: Optional[str]


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
    consistent_snapshot: Optional[bool]
    roles: Optional[Dict[Roles.values(), TUFSignedRoles]]
    meta: Optional[Dict[str, TUFSignedMetaFile]]
    targets: Optional[Dict[str, str]]
    delegations: Optional[TUFSignedDelegations]

    class Config:
        fields = {"type": "_type"}
        # https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra
        model_config = ConfigDict(
            extra="allow",
        )
        extra = (
            Extra.allow
        )  # allow extra unrecognized fields (but it will be validated)

    # Custom Validator for the extra fields (TUF unrecognized_fields)
    @root_validator(pre=True)
    def validate_unrecognized_fields(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        all_required_field_names = {
            field.alias
            for field in cls.__fields__.values()
            if field.alias != "extra"  # to support alias
        }

        for field_name in list(values):
            if field_name not in all_required_field_names:
                if (
                    not field_name.startswith("x")
                    or len(field_name.split("-")) < 3
                ):
                    raise ValueError(
                        f"Invalid: `{field_name}` field name, "
                        "unrecognized_field must use format x-<vendor>-<name>"
                    )
        return values


class TUFSignatures(BaseModel):
    keyid: str
    sig: str


class TUFMetadata(BaseModel):
    signatures: List[TUFSignatures]
    signed: TUFSigned
