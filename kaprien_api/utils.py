from typing import Any, Dict, Optional

from dynaconf import loaders
from dynaconf.utils.boxing import DynaBox
from pydantic import BaseModel, Field

from kaprien_api import SETTINGS_FILE, settings


class BaseErrorResponse(BaseModel):
    error: str = Field(description="Error message")
    details: Optional[Dict[str, str]] = Field(description="Error details")
    code: Optional[int] = Field(description="Error code if available")


def save_settings(key: str, value: Any):
    settings.store[key] = value
    settings_data = settings.as_dict(env=settings.current_env)
    loaders.write(
        SETTINGS_FILE,
        DynaBox(settings_data).to_dict(),
        env=settings.current_env,
    )
