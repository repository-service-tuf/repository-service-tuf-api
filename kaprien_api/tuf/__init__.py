import enum

from securesystemslib.exceptions import StorageError  # noqa
from tuf.api.metadata import (  # noqa
    TOP_LEVEL_ROLE_NAMES,
    DelegatedRole,
    Key,
    Metadata,
    Root,
    Snapshot,
    Targets,
    Timestamp,
)
from tuf.api.serialization.json import JSONSerializer  # noqa

from kaprien_api.tuf import services  # noqa
from kaprien_api.tuf.interfaces import (  # noqa
    IKeyVault,
    IStorage,
    ServiceSettings,
)


class Roles(enum.Enum):
    ROOT = Root.type
    TARGETS = Targets.type
    SNAPSHOT = Snapshot.type
    TIMESTAMP = Timestamp.type
    BIN = "bin"
    BINS = "bins"


ALL_REPOSITORY_ROLES_NAMES = [rolename.value for rolename in Roles]
OFFLINE_KEYS = {
    Roles.ROOT.value.upper(),
    Roles.TARGETS.value.upper(),
    Roles.BIN.value.upper(),
}
