from fastapi import APIRouter, Depends, Security
from fastapi.security import OAuth2PasswordRequestForm

from kaprien_api import token

router = APIRouter(
    prefix="/token",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/", description="Return tokens", response_model=token.PostTokenResponse
)
def post(
    token_data: OAuth2PasswordRequestForm = Depends(),
    params: token.PostParameters = Depends(),
):
    return token.post(token_data, params)


@router.get(
    "/",
    response_model=token.GetTokenResponse,
    response_model_exclude_none=True,
)
def get(
    params: token.GetParameters = Depends(),
    _user=Security(token.validate_token, scopes=["read:token"]),
):
    return token.get(params)
