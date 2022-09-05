from fastapi import APIRouter, Security, status

from kaprien_api import SCOPES_NAMES, targets
from kaprien_api.token import validate_token

router = APIRouter(
    prefix="/targets",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    summary=(
        "Add targets files to Metadata. "
        f"Scope: {SCOPES_NAMES.write_bootstrap.value}"
    ),
    description="Add targets files to Metadata.",
    response_model=targets.Response,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def post(
    payload: targets.Payload,
    _user=Security(validate_token, scopes=[SCOPES_NAMES.write_targets.value]),
):
    return targets.post(payload)
