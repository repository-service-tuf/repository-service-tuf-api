from fastapi import APIRouter

from kaprien_api import targets

router = APIRouter(
    prefix="/targets",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    description="Add targets files to Metadata",
    response_model=targets.Response,
    response_model_exclude_none=True,
)
def post(payload: targets.Payload):
    return targets.post(payload)