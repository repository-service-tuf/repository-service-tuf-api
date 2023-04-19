# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from datetime import datetime, timedelta
from typing import List, Literal, Optional
from uuid import uuid4

from fastapi import Depends, HTTPException, Query, status
from fastapi.param_functions import Form
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import BaseModel, Field, SecretStr, ValidationError

from repository_service_tuf_api import SCOPES, SCOPES_NAMES, SECRET_KEY, db
from repository_service_tuf_api.users.crud import bcrypt, get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token", scopes=SCOPES)


class TokenRequestForm:
    def __init__(
        self,
        username: str = Form(),
        password: SecretStr = Form(),
        scope: str = Form(
            description=(
                "Add scopes separeted by space. "
                "Available scopes: "
                f"{', '.join([f'`{scope.value}`' for scope in SCOPES_NAMES])}"
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
                "scopes": [scope.value for scope in SCOPES_NAMES],
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
            SCOPES_NAMES.read_bootstrap.value,
            SCOPES_NAMES.read_settings.value,
            SCOPES_NAMES.read_tasks.value,
            SCOPES_NAMES.read_token.value,
            SCOPES_NAMES.write_targets.value,
            SCOPES_NAMES.delete_targets.value,
        ]
    ] = Field(min_items=1)
    expires: int = Field(description="In hour(s)", ge=1)

    class Config:
        example = {
            "scopes": [
                SCOPES_NAMES.read_token.value,
                SCOPES_NAMES.read_settings.value,
            ],
            "expires": 24,
        }

        schema_extra = {"example": example}


def _decode_token(token):
    try:
        user_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except (JWTError, ValidationError):
        raise ValueError("Token cannot be decoded.")
    return user_token


def create_access_token(data: dict, expires_delta: int = 1):
    to_encode = data.copy()
    expires = datetime.utcnow() + timedelta(hours=expires_delta)

    to_encode.update({"exp": expires})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

    return encoded_jwt


def validate_token(
    security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)
):
    try:
        user_token = _decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": ("Failed to validate token")},
        )

    if any(
        scope
        for scope in security_scopes.scopes
        if scope not in user_token.get("scopes", [])
    ):
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
    user = get_user_by_username(db, token_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    elif not bcrypt.checkpw(
        token_data.password.encode("utf-8"), user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    for scope in token_data.scope:
        if scope not in [sc.name for sc in user.scopes]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": f"scope '{scope}' forbidden"},
            )

    # return data with requested scopes -- approved :D
    data = {
        "sub": f"user_{user.id}_{uuid4().hex}",
        "username": user.username,
        "password": str(user.password),
        "scopes": token_data.scope,
    }
    access_token = create_access_token(
        data=data,
        expires_delta=token_data.expires,
    )

    return {"access_token": access_token}


def post_new(payload, user):
    db_user = get_user_by_username(db, user["username"])
    data = {
        "sub": f"user_{db_user.id}_{uuid4().hex}",
        "username": db_user.username,
        "password": str(db_user.password),
        "scopes": payload.scopes,
    }
    token = create_access_token(data=data, expires_delta=payload.expires)

    return {"access_token": token}


def get(params):
    try:
        token = _decode_token(params.token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={"error": ("Failed to validate token")},
        )
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
