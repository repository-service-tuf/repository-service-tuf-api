from fastapi import APIRouter, Depends, Security

from kaprien_api import SCOPES_NAMES, token

router = APIRouter(
    prefix="/token",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    summary=("Get token details. " f"Scope: {SCOPES_NAMES.read_token.value}"),
    description=(
        "Return the token details. It requires an authenticated token with "
        "scope authorization."
    ),
    response_model=token.GetTokenResponse,
    response_model_exclude_none=True,
)
def get(
    params: token.GetParameters = Depends(),
    _user=Security(
        token.validate_token, scopes=[SCOPES_NAMES.read_token.value]
    ),
):
    return token.get(params)


@router.post(
    "/",
    summary="Issue token user/password authentication",
    description="Issue a token with scopes for all granted user scope.",
    response_model=token.PostTokenResponse,
)
def post(
    token_data: token.TokenRequestForm = Depends(),
):
    return token.post(token_data)


@router.post(
    "/new/",
    summary=(
        "Issue token from authenticated token. "
        f"Scope: {SCOPES_NAMES.write_token.value}"
    ),
    description="Issue token from a valid and existent token.",
    response_model=token.PostTokenResponse,
    status_code=200,
)
def post_token(
    payload: token.TokenRequestPayload,
    user=Security(
        token.validate_token, scopes=[SCOPES_NAMES.write_token.value]
    ),
):
    return token.post_new(payload=payload, user=user)
