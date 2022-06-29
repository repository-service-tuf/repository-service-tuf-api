from fastapi import APIRouter

from kaprien_api import bootstrap

router = APIRouter(
    prefix="/bootstrap",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    response_model=bootstrap.BootstrapResponse,
    response_model_exclude_none=True,
)
def get():
    return bootstrap.get_bootstrap()


@router.post(
    "/",
    response_model=bootstrap.BootstrapResponse,
    response_model_exclude_none=True,
)
def post(payload: bootstrap.BootstrapPayload):
    return bootstrap.post_bootstrap(payload)
