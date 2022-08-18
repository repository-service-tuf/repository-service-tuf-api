from fastapi import APIRouter, Security

from kaprien_api import targets
from kaprien_api.token import validate_token

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
def post(
    payload: targets.Payload,
    _user=Security(validate_token, scopes=["write:targets"]),
):
    return targets.post(payload)
