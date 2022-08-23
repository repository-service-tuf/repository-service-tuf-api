from fastapi import APIRouter, Depends, Security

from kaprien_api import SCOPES_NAMES, token

router = APIRouter(
    prefix="/token",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
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
    description="Issue token user/password authentication",
    response_model=token.PostTokenResponse,
)
def post(
    token_data: token.TokenRequestForm = Depends(),
):
    return token.post(token_data)


@router.post(
    "/new/",
    summary="Issue token from token.",
    status_code=200,
    description=(
        "Issue token by an authenticated token."
        f"Requires scope '{SCOPES_NAMES.read_token.value}'"
    ),
    response_model=token.PostTokenResponse,
)
def post_token(
    payload: token.TokenRequestPayload,
    user=Security(
        token.validate_token, scopes=[SCOPES_NAMES.write_token.value]
    ),
):
    return token.post_new(payload=payload, user=user)
