from fastapi import APIRouter

from kaprien_api import repository_settings

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
def get():
    return repository_settings.get()
