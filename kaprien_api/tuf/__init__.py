import enum

from kaprien_api.tuf.hash_bins import HashBins
from kaprien_api.tuf.interfaces import IKeyVault, IStorage, ServiceSettings
from kaprien_api.tuf.repository import (
    TOP_LEVEL_ROLE_NAMES,
    DelegatedRole,
    JSONSerializer,
    Key,
    Metadata,
    MetadataRepository,
    Root,
    Snapshot,
    Targets,
    Timestamp,
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


__all__ = [
    HashBins,
    IKeyVault,
    IStorage,
    Metadata,
    MetadataRepository,
    DelegatedRole,
    TOP_LEVEL_ROLE_NAMES,
    JSONSerializer,
    MetadataRepository,
    Timestamp,
    Targets.__name__,
    ServiceSettings,
    Key,
]
