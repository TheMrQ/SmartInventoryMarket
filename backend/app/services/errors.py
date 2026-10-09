"""Domain errors translated to non-sensitive HTTP responses at the API boundary."""


class DomainError(Exception):
    status_code = 409


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409
