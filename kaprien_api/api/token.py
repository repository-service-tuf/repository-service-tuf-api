import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from kaprien_api import db
from kaprien_api.token import GetParameters, create_access_token
from kaprien_api.users.crud import get_user_by_username

router = APIRouter(
    prefix="/token",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", description="Return tokens")
def get(
    data: OAuth2PasswordRequestForm = Depends(),
    params: GetParameters = Depends(),
):
    user = get_user_by_username(db, data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    elif data.password != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    for scope in data.scopes:
        if scope not in [scope.name for scope in user.scopes]:
            logging.debug(f"User '{user}' forbidden for '{scope}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": f"scope '{scope}' forbidden"},
            )

    # return data with requested scopes -- approved :D
    data = {
        "sub": f"user_{user.id}",
        "username": user.username,
        "password": user.password,
        "scopes": data.scopes,
    }
    access_token = create_access_token(
        data=data,
        expires_delta=timedelta(hours=params.expires),
    )
    return {"access_token": access_token}
