# SPDX-FileCopyrightText: 2023-2024 Repository Service for TUF Contributors
# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from repository_service_tuf_api import settings_repository


class Roles(Enum):
    ROOT = "root"
    TARGETS = "targets"
    SNAPSHOT = "snapshot"
    TIMESTAMP = "timestamp"
    BINS = "bins"

    @staticmethod
    def is_role(input: Any) -> bool:
        if not isinstance(input, str):
            return False

        return any(input == role.value for role in Roles)

    @staticmethod
    def all_str() -> str:
        return "root, targets, snapshot, timestamp and bins"

    @staticmethod
    def values() -> List[str]:
        return Literal["root", "targets", "snapshot", "timestamp", "bins"]

    @staticmethod
    def online_roles_values() -> List[str]:
        online_roles: List[str] = ["snapshot", "timestamp"]
        if settings_repository.get_fresh("TARGETS_ONLINE_KEY", True):
            online_roles.append("targets")

        delegated_roles: List[str] = settings_repository.get_fresh(
            "DELEGATED_ROLES_NAMES"
        )
        # All delegated roles names should start with "bins" if we are using
        # hash bin delegation and none of the delegated roles should start with
        # "bins" if we are using custom target delegation.
        bins_used = True if delegated_roles[0].startswith("bins") else False
        if bins_used:
            online_roles.append(Roles.BINS.value)
        else:
            online_roles.extend(delegated_roles)

        return online_roles


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
    x_rstuf_expire_policy: int = Field(
        alias="x-rstuf-expire-policy",
        description="Expire Policy for the role",
        default=None,
    )
    x_rstuf_num_bins: int = Field(
        alias="x-rstuf-num-bins",
        description="Number of bins for nested hash-bin roles",
        default=None,
    )
    x_rstuf_role_online_key: str | None = Field(
        alias="x-rstuf-role-online-key",
        description=(
            "Keyid of the online key signing this role's nested hash bins. "
            "The key is declared in `delegations.keys`. It never signs the "
            "role itself, so it is not listed in `keyids`."
        ),
        default=None,
    )
    # Note: No validation is required for paths as these patterns are only used
    # to distribute artifacts. No files are created based on them.
    paths: List[str] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def validate_path_patterns(cls, values: Dict[str, Any]):
        path_patterns = values.get("paths")
        if any(len(pattern) < 1 for pattern in path_patterns):
            raise ValueError("No empty strings are allowed as path patterns")

        return values

    @model_validator(mode="after")
    def validate_nested_bins(self) -> "TUFSignedDelegationsRoles":
        num_bins = self.x_rstuf_num_bins
        if num_bins is not None:
            if num_bins < 2 or num_bins & (num_bins - 1) != 0:
                raise ValueError(
                    f"Role {self.name!r} x-rstuf-num-bins must be a power "
                    "of 2 greater than 1"
                )
            # The Worker generates and signs the bins, so it must be able to
            # sign their delegator too: threshold 1, online key.
            if self.threshold != 1:
                raise ValueError(
                    f"Role {self.name!r} nested hash bins require threshold 1"
                )

        if self.x_rstuf_role_online_key is not None:
            if num_bins is None:
                raise ValueError(
                    f"Role {self.name!r} declares x-rstuf-role-online-key "
                    "without x-rstuf-num-bins; the key only ever signs the "
                    "role's nested hash bins"
                )
            if self.x_rstuf_role_online_key in self.keyids:
                raise ValueError(
                    f"Role {self.name!r} x-rstuf-role-online-key must not "
                    "be one of the role's own keyids: a delegation cannot "
                    "sign itself"
                )

        return self


class TUFSignedDelegationsSuccinctRoles(BaseModel):
    bit_length: int = Field(gt=0, lt=15)
    name_prefix: str
    keyids: List[str]
    threshold: int


class TUFKeys(BaseModel):
    keytype: str
    scheme: str
    keyval: Dict[Literal["public", "issuer", "identity"], str]
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

        for field_name in values:
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
    bundle: Dict[str, Any] | None = None


class TUFMetadata(BaseModel):
    signatures: List[TUFSignatures]
    signed: TUFSigned


# URI schemes the Worker can resolve to a signer (securesystemslib's
# SIGNER_FOR_URI_SCHEME plus RSTUF's own file-name signer). A role online key
# may only use one of these: the scheme selects the signer backend, so an
# unknown scheme is unusable and an unrestricted one would let a request point
# the Worker at an arbitrary backend.
ALLOWED_ONLINE_KEY_URI_SCHEMES = frozenset(
    {
        "fn",
        "envvar",
        # securesystemslib's current CryptoSigner file scheme (the Worker's
        # signer resolver registers "file2", not "file")
        "file",
        "file2",
        "awskms",
        "gcpkms",
        "azurekms",
        "hv",
        "sigstore",
    }
)


class TUFDelegations(BaseModel):
    keys: Dict[str, TUFKeys]
    roles: List[TUFSignedDelegationsRoles]

    @model_validator(mode="after")
    def validate_role_online_keys(self) -> "TUFDelegations":
        """Check that every declared role online key is usable.

        A role online key signs the hash bins nested below its role, so the
        Worker must be able to resolve it to a signer, and no role may list
        it among its own keyids.
        """
        names = [role.name for role in self.roles]
        if len(names) != len(set(names)):
            raise ValueError("Delegations contain duplicate role names")

        all_keyids = {keyid for role in self.roles for keyid in role.keyids}
        for role in self.roles:
            keyid = role.x_rstuf_role_online_key
            if keyid is None:
                continue

            key = self.keys.get(keyid)
            if key is None:
                raise ValueError(
                    f"Role {role.name!r} x-rstuf-role-online-key {keyid!r} "
                    "is not declared in delegations.keys"
                )

            uri = key.x_rstuf_online_key_uri
            if not uri:
                raise ValueError(
                    f"Role {role.name!r} online key {keyid!r} has no "
                    "x-rstuf-online-key-uri; the Worker cannot sign with it"
                )

            scheme = uri.split(":", 1)[0]
            if scheme not in ALLOWED_ONLINE_KEY_URI_SCHEMES:
                allowed = ", ".join(sorted(ALLOWED_ONLINE_KEY_URI_SCHEMES))
                raise ValueError(
                    f"Role {role.name!r} online key {keyid!r} uses "
                    f"unsupported URI scheme {scheme!r}; allowed schemes: "
                    f"{allowed}"
                )

            if keyid in all_keyids:
                raise ValueError(
                    f"Role online key {keyid!r} must not be used to sign a "
                    "delegated role; it only signs nested hash bins"
                )

        return self
