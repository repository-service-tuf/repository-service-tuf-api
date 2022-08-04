import json
from typing import Any, Dict, List, Optional

from kaprien_api.utils import BaseModel


class Response(BaseModel):
    data: Optional[List[str]]
    message: Optional[str]

    class Config:
        data_example = {
            "data": {"targets": ["file1.tar.gz", "file2.tar.gz"]},
            "message": "Target files successfully added.",
        }
        schema_extra = {"example": data_example}


class PayloadTargetsHashes(BaseModel):
    blake2b_256: str

    class Config:
        fields = {"blake2b_256": "blake2b-256"}


class TargetsInfo(BaseModel):
    length: int
    hashes: PayloadTargetsHashes
    custom: Optional[Dict[str, Any]]


class Targets(BaseModel):
    info: TargetsInfo
    path: str


class Payload(BaseModel):
    targets: List[Targets]

    class Config:
        with open("tests/data_examples/targets/payload.json") as f:
            content = f.read()
        payload = json.loads(content)
        schema_extra = {"example": payload}


def post(payload):

    # TODO: Implement the publisher to the kaprien-mq (issue #39)
    data = [target.path for target in payload.targets]
    return Response(data=data, message="Target file(s) successfully added.")
