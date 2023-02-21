# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import List, Literal, Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.param_functions import Form
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pydantic import BaseModel, Field, SecretStr

from repository_service_tuf_api import auth_service
from repository_service_tuf_api.rstuf_auth import exceptions as auth_exceptions
from repository_service_tuf_api.rstuf_auth.enums import ScopeName
from repository_service_tuf_api.rstuf_auth.services.auth import \
    SCOPES_DESCRIPTION

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/token", scopes=SCOPES_DESCRIPTION
)


class TokenRequestForm:
    def __init__(
        self,
        username: str = Form(),
        password: SecretStr = Form(),
        scope: str = Form(
            description=(
                "Add scopes separeted by space. "
                "Available scopes: "
                f"{', '.join([f'`{scope}`' for scope in ScopeName])}"
            ),
        ),
        expires: Optional[int] = Form(
            default=1,
            description="Expiration in hours. Default: 1 hour",
            ge=1,
        ),
    ):
        self.username = username
        self.password = password.get_secret_value()
        self.scope = scope.split()
        self.expires = expires


class GetParameters:
    def __init__(
        self,
        token: str = Query(description="Token to be validated", required=True),
    ):
        self.token = token


class TokenPublicData(BaseModel):
    scopes: Optional[List[str]]
    expired: bool
    expiration: Optional[datetime]


class GetTokenResponse(BaseModel):
    data: TokenPublicData
    message: str

    class Config:
        example = {
            "data": {
                "scopes": [scope.value for scope in ScopeName],
                "expired": False,
                "expiration": "2022-08-19T17:29:39",
            },
            "message": "Token information",
        }
        schema_extra = {"example": example}


class PostTokenResponse(BaseModel):
    access_token: str

    class Config:
        example = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJz...fhpp0"
        }
        schema_extra = {"example": example}


class TokenRequestPayload(BaseModel):
    scopes: List[
        Literal[
            ScopeName.read_bootstrap,
            ScopeName.read_settings,
            ScopeName.read_tasks,
            ScopeName.read_token,
            ScopeName.write_targets,
            ScopeName.delete_targets,
        ]
    ] = Field(min_items=1)
    expires: int = Field(description="In hour(s)", ge=1)

    class Config:
        example = {
            "scopes": [
                ScopeName.read_token,
                ScopeName.read_settings,
            ],
            "expires": 24,
        }

        schema_extra = {"example": example}


def validate_token(
    security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)
) -> dict | None:
    if not auth_service:
        return None

    try:
        user_token = auth_service.validate_token(token, security_scopes.scopes)
    except auth_exceptions.InvalidTokenFormat:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Failed to validate token"},
        )
    except auth_exceptions.ScopeNotProvided:
        # TODO: the error message should be scope not found/provided
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": (
                    f"scope '{', '.join(security_scopes.scopes)}' not allowed"
                )
            },
        )

    return user_token


def post(token_data):

    try:
        token = auth_service.issue_token(
            token_data.username,
            password=token_data.password,
            scopes=token_data.scope,
            expires_delta=token_data.expires,
        )

    except auth_exceptions.UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    except auth_exceptions.InvalidPassword:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    except auth_exceptions.ScopeNotFoundInUserScopes as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": f"scope '{e.scope}' forbidden"},
        )

    return {"access_token": token.access_token}


def post_new(payload, username):
    try:
        token = auth_service.issue_token(
            username, payload.scopes, payload.expires
        )

    except auth_exceptions.UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    except auth_exceptions.ScopeNotFoundInUserScopes as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": f"scope '{e.scope}' forbidden"},
        )

    return {"access_token": token.access_token}


def get(params):
    try:
        token = auth_service.validate_token(params.token)
    except auth_exceptions.InvalidTokenFormat:
        # TODO: must be 401?
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={"error": "Failed to validate token"},
        )

    # TODO: should we move this to the auth service?
    expires = datetime.fromtimestamp(token.get("exp"))

    if expires < datetime.now():
        expired = True
    else:
        expired = False

    data = TokenPublicData(
        scopes=token.get("scopes"),
        expired=expired,
        expiration=datetime.fromtimestamp(token.get("exp")),
    )

    return GetTokenResponse(data=data, message="Token information")
