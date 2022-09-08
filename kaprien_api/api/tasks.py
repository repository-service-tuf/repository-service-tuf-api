from fastapi import APIRouter, Depends, Security

from kaprien_api import SCOPES_NAMES, tasks
from kaprien_api.token import validate_token

router = APIRouter(
    prefix="/task",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    summary=("Get task status. " f"Scope: {SCOPES_NAMES.read_tasks.value}"),
    description=(
        "Get Repository Metadata task status. "
        "The status is according with Celery tasks: "
        "`PENDING` the task still not processed or unknown/inexistent task. "
        "`RECEIVED` task is reveived by the broker server. "
        "`PRE_RUN` the task will start by kaprien-repo-worker. "
        "`RUNNING` the task is in execution. "
        "`FAILURE` the task failed to executed. "
        "`SUCCESS` the task execution is finished. "
    ),
    response_model=tasks.Response,
    response_model_exclude_none=True,
)
def get(
    params: tasks.GetParameters = Depends(),
    _user=Security(validate_token, scopes=[SCOPES_NAMES.read_tasks.value]),
):
    return tasks.get(params.task_id)
