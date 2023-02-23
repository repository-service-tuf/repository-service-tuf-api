# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

from repository_service_tuf_api import auth_service
from repository_service_tuf_api.rstuf_auth import exceptions as auth_exceptions
from repository_service_tuf_api.rstuf_auth.services.auth import (
    SCOPES_DESCRIPTION,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/token", scopes=SCOPES_DESCRIPTION
)


def authorize_user(
    security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)
) -> dict | None:
    if auth_service is None:
        return None

    try:
        user_token = auth_service.validate_token(token, security_scopes.scopes)
    except auth_exceptions.InvalidTokenFormat:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Failed to validate token"},
        )
    except auth_exceptions.UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    except auth_exceptions.ScopeNotProvided:
        # TODO: the error message should be "scope not found/provided"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": (
                    f"scope '{', '.join(security_scopes.scopes)}' not allowed"
                )
            },
        )

    return {"username": user_token.username, "scopes": user_token.scopes}
