from typing import Optional

from repository_service_tuf_api.rstuf_auth.ports.auth import (
    AuthenticationService,
)
from repository_service_tuf_api.rstuf_auth.services.auth import (
    CustomSQLAuthenticationService,
)
from repository_service_tuf_api.rstuf_auth.services.fake import (
    FakeAuthenticationService,
)


def config(
    settings,
    secrets_settings,
    base_dir: str,
    scopes: dict[str, str],
    is_auth_enabled: bool = False,
    env: Optional[str] = None,
):
    auth_service: Optional[AuthenticationService] = None

    if is_auth_enabled:
        if env == "testing":
            auth_service = FakeAuthenticationService(scopes=scopes)
        else:
            auth_service = CustomSQLAuthenticationService(
                settings=settings,
                secrets_settings=secrets_settings,
                base_dir=base_dir,
                scopes=scopes,
            )

    return auth_service
