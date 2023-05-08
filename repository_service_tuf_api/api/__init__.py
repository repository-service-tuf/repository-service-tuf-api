# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT

import logging
from typing import Callable

from repository_service_tuf_api import is_auth_enabled
from repository_service_tuf_api.token import validate_token


def get_auth() -> Callable:
    if is_auth_enabled is True:
        logging.info("RSTUF builtin auth is enabled")
        return validate_token
    else:
        logging.info("RSTUF builtin auth is disabled")
        return lambda: None
