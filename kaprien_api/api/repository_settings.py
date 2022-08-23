from fastapi import APIRouter, Security

from kaprien_api import SCOPES_NAMES, repository_settings
from kaprien_api.token import validate_token

router = APIRouter(
    prefix="/settings",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    description="Returns the Settings",
    response_model=repository_settings.Response,
    response_model_exclude_none=True,
)
def get(
    _user=Security(validate_token, scopes=[SCOPES_NAMES.read_settings.value])
):
    return repository_settings.get()
