class PolitikontrollerError(Exception):
    pass


class PolitikontrollerConnectionError(PolitikontrollerError):
    pass


class PolitikontrollerTimeoutError(PolitikontrollerConnectionError):
    pass


class NoAccessError(PolitikontrollerError):
    pass


class NotFoundError(PolitikontrollerError):
    pass


class NoContentError(PolitikontrollerError):
    pass


class AuthenticationError(PolitikontrollerError):
    pass


class AuthenticationBlockedError(AuthenticationError):
    pass


class NotActivatedError(AuthenticationError):
    pass
