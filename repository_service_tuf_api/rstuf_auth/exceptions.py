class UserNotFound(Exception):
    pass


class InvalidPassword(Exception):
    pass


class ScopeNotFoundInUserScopes(Exception):
    def __init__(self, scope=None):
        self.scope = scope


class ScopeNotProvided(Exception):
    def __init__(self, scope=None):
        self.scope = scope


class InvalidTokenFormat(Exception):
    pass


class SecretKeyNotFoundInSettings(Exception):
    pass


class AdminPasswordNotFoundInSettings(Exception):
    pass


class UserAlreadyExists(Exception):
    pass
