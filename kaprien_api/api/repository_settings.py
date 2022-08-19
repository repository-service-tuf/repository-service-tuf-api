from fastapi import APIRouter, Security

from kaprien_api import repository_settings
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
def get(_user=Security(validate_token, scopes=["read:settings"])):
    return repository_settings.get()
