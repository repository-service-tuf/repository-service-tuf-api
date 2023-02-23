# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import List, Literal, Optional

from fastapi import HTTPException, Query, status
from fastapi.param_functions import Form
from pydantic import BaseModel, Field, SecretStr

from repository_service_tuf_api import auth_service
from repository_service_tuf_api.rstuf_auth import exceptions as auth_exceptions
from repository_service_tuf_api.rstuf_auth.enums import ScopeName


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
                "scopes": [scope for scope in ScopeName],
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


def get(token_to_validate):
    """Gets a token, validates it and return its information"""
    try:
        token = auth_service.validate_token(token_to_validate)
    except (auth_exceptions.InvalidTokenFormat, auth_exceptions.UserNotFound):
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={"error": "Failed to validate token"},
        )

    expires = datetime.fromtimestamp(token.expires_at)

    if expires < datetime.now():
        expired = True
    else:
        expired = False

    data = TokenPublicData(
        scopes=token.scopes,
        expired=expired,
        expiration=datetime.fromtimestamp(token.expires_at),
    )

    return GetTokenResponse(data=data, message="Token information")
