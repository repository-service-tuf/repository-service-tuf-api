from fastapi import APIRouter, Security

from kaprien_api import SCOPES_NAMES, config
from kaprien_api.token import validate_token

router = APIRouter(
    prefix="/config",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    summary=("List settings. " f"Scope: {SCOPES_NAMES.read_settings.value}"),
    description="Returns the configuration settings",
    response_model=config.Response,
    response_model_exclude_none=True,
)
def get(
    _user=Security(validate_token, scopes=[SCOPES_NAMES.read_settings.value])
):
    return config.get()
