from enum import Enum


class ScopeName(str, Enum):
    read_bootstrap = "read:bootstrap"
    read_settings = "read:settings"
    read_tasks = "read:tasks"
    read_token = "read:token"  # nosec bandit: not hard coded password
    write_bootstrap = "write:bootstrap"
    write_targets = "write:targets"
    write_token = "write:token"  # nosec bandit: not hard coded password
    delete_targets = "delete:targets"
