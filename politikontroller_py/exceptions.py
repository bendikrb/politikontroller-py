class PolitikontrollerError(Exception):
    pass


class NoAccessError(PolitikontrollerError):
    pass


class NoContentError(PolitikontrollerError):
    pass


class AuthenticationError(PolitikontrollerError):
    pass


class AuthenticationBlockedError(AuthenticationError):
    pass


class NotActivatedError(AuthenticationError):
    pass
