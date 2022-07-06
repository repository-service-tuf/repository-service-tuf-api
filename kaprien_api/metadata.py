import glob
import json
from typing import Dict, Optional, Union

from fastapi import HTTPException, Query, status
from securesystemslib.exceptions import StorageError

from kaprien_api import tuf, tuf_repository
from kaprien_api.tuf import TOP_LEVEL_ROLE_NAMES
from kaprien_api.utils import BaseModel, TUFMetadata


class GetParameters:
    def __init__(
        self,
        rolename: Union[str, None] = Query(
            default=None, description="Specific rolename Metadata"
        ),
    ):

        self.rolename = rolename


class Response(BaseModel):
    data: Optional[Dict[str, TUFMetadata]]
    message: Optional[str]

    class Config:
        metadata_files = glob.glob("tests/data_examples/metadata/*.json")
        metadata: dict = dict()
        for metadata_file in metadata_files:
            with open(metadata_file) as f:
                content = f.read()
                example_metadata = json.loads(content)
            filename = metadata_file.split("/")[-1].replace(".json", "")
            metadata[filename] = example_metadata

        schema_extra = {"example": metadata}


def get(params: GetParameters) -> Optional[Dict[str, tuf.Metadata]]:
    if tuf_repository.is_initialized is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "No metadata found in the Storage."},
        )

    metadata: Dict[str, tuf.Metadata] = dict()

    try:
        if params.rolename:
            metadata[params.rolename] = tuf_repository.load_role(
                params.rolename
            ).to_dict()
            return Response(data=metadata)

    except StorageError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": str(err)},
        )

    for role in TOP_LEVEL_ROLE_NAMES:
        metadata[role] = tuf_repository.load_role(role).to_dict()

    bin_metadata = tuf_repository.load_role(tuf.Roles.BIN.value)
    metadata[tuf.Roles.BIN.value] = bin_metadata.to_dict()
    for role in bin_metadata.signed.delegations.roles:
        metadata[role] = tuf_repository.load_role(role).to_dict()

    return Response(data=metadata)
