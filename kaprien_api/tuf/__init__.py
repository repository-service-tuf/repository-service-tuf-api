import enum

from securesystemslib.exceptions import StorageError  # noqa

from kaprien_api.tuf.interfaces import (  # noqa
    IKeyVault,
    IStorage,
    ServiceSettings,
)


class Roles(enum.Enum):
    ROOT = "root"
    TARGETS = "targets"
    SNAPSHOT = "snapshot"
    TIMESTAMP = "timestamp"
    BIN = "bin"
    BINS = "bins"


ALL_REPOSITORY_ROLES_NAMES = [rolename.value for rolename in Roles]
OFFLINE_KEYS = {
    Roles.ROOT.value.upper(),
    Roles.TARGETS.value.upper(),
    Roles.BIN.value.upper(),
}
