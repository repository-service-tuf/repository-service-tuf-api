from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import ValidationError

from kaprien_api import SCOPES, SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token", scopes=SCOPES)


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
        user_payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": ("Failed to validate token")},
        )

    if any(
        scope
        for scope in security_scopes.scopes
        if scope not in user_payload.get("scopes", [])
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": (
                    f"scope '{', '.join(security_scopes.scopes)}' not allowed"
                )
            },
        )
    return user_payload


class GetParameters:
    def __init__(
        self,
        expires: int = Query(
            default=1, description="Token expiration in days"
        ),
    ):

        self.expires = expires
