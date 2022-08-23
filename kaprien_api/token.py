from datetime import datetime, timedelta
from typing import List, Optional, Union

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import ValidationError

from kaprien_api import SCOPES, SECRET_KEY, db
from kaprien_api.users.crud import get_user_by_username
from kaprien_api.utils import BaseModel, uuid4

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token", scopes=SCOPES)


class PostParameters:
    def __init__(
        self,
        expires: int = Query(
            default=1, description="Token expiration in hour(s)"
        ),
    ):

        self.expires = expires


class GetParameters:
    def __init__(
        self,
        token: str = Query(description="Token to be validated"),
        required=True,
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
                "scopes": [
                    "read:targets",
                    "read:bootstrap",
                    "read:settings",
                    "read:token",
                    "write:targets",
                    "write:bootstrap",
                ],
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


def _decode_token(token):
    try:
        user_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except (JWTError, ValidationError):
        raise ValueError("Token cannot be decoded.")
    return user_token


def create_access_token(
    data: dict, expires_delta: Union[timedelta, None] = None
):

    to_encode = data.copy()
    expires = datetime.utcnow() + expires_delta

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


def post(token_data, params):
    user = get_user_by_username(db, token_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    elif token_data.password != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    for scope in token_data.scopes:
        if scope not in [scope.name for scope in user.scopes]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": f"scope '{scope}' forbidden"},
            )

    # return data with requested scopes -- approved :D
    data = {
        "sub": f"user_{user.id}_{uuid4().hex}",
        "username": user.username,
        "password": user.password,
        "scopes": token_data.scopes,
    }
    access_token = create_access_token(
        data=data,
        expires_delta=timedelta(hours=params.expires),
    )

    return {"access_token": access_token}


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
