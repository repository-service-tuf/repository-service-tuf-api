from fastapi import APIRouter, Depends

from kaprien_api import metadata

router = APIRouter(
    prefix="/metadata",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    description="Returns the Repository Metadada",
    response_model=metadata.Response,
    response_model_exclude_none=True,
)
def get(params: metadata.GetParameters = Depends()):
    return metadata.get(params)
