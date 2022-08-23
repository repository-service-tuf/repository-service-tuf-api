from fastapi import APIRouter, Security, status

from kaprien_api import SCOPES_NAMES, bootstrap
from kaprien_api.token import validate_token

router = APIRouter(
    prefix="/bootstrap",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    response_model=bootstrap.BootstrapGetResponse,
    response_model_exclude_none=True,
)
def get(
    _user=Security(validate_token, scopes=[SCOPES_NAMES.read_bootstrap.value])
):
    return bootstrap.get_bootstrap()


@router.post(
    "/",
    response_model=bootstrap.BootstrapPostResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post(
    payload: bootstrap.BootstrapPayload,
    _user=Security(
        validate_token, scopes=[SCOPES_NAMES.write_bootstrap.value]
    ),
):
    return bootstrap.post_bootstrap(payload)
