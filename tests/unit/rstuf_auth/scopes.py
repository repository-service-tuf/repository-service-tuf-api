from enum import Enum


class ScopeName(str, Enum):
    read_bootstrap = "read:bootstrap"
    write_bootstrap = "write:bootstrap"


SCOPES_DESCRIPTION = {
    ScopeName.read_bootstrap: "Read (GET) bootstrap",
    ScopeName.write_bootstrap: "Write (POST) bootstrap",
}
