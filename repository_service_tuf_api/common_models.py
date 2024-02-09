# SPDX-FileCopyrightText: 2023-2024 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    details: Dict[str, str] | None = Field(
        description="Error details", default=None
    )
    code: int | None = Field(
        description="Error code if available", default=None
    )


class TUFSignedDelegationsRoles(BaseModel):
    name: str
    terminating: bool
    keyids: List[str]
    threshold: int
    paths: List[str] | None = None
    path_hash_prefixes: List[str] | None = None


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
    keyval: Dict[Literal["public"], str]
    name: str | None = Field(
        description="Use x-rstuf-key-name instead. Key Name",
        default=None,
    )
    x_rstuf_key_name: str | None = Field(
        alias="x-rstuf-key-name", description="Key Name", default=None
    )
    x_rstuf_online_key_uri: Optional[str] = Field(
        alias="x-rstuf-online-key-uri",
        description="Online Key URI",
        default=None,
    )


class TUFSignedDelegations(BaseModel):
    keys: Dict[str, TUFKeys]
    roles: List[TUFSignedDelegationsRoles] | None
    succinct_roles: TUFSignedDelegationsSuccinctRoles | None


class TUFSignedMetaFile(BaseModel):
    version: int


class TUFSignedRoles(BaseModel):
    keyids: List[str]
    threshold: int


class TUFSigned(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )

    type: str = Field(alias="_type")
    version: int
    spec_version: str
    expires: str
    keys: Dict[str, TUFKeys] | None = None
    consistent_snapshot: bool | None = None
    roles: Dict[Roles.values(), TUFSignedRoles] | None = None
    meta: Dict[str, TUFSignedMetaFile] | None = None
    targets: Dict[str, str] | None = None
    delegations: TUFSignedDelegations | None = None

    # Custom Validator for the extra fields (TUF unrecognized_fields)
    @model_validator(mode="before")
    @classmethod
    def validate_unrecognized_fields(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        all_required_field_names = {
            v.alias or f for f, v in cls.model_fields.items()
        }

        for field_name in list(values.keys()):
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
