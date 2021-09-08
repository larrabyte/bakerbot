class SecretNotFound(Exception):
    """Raise this exception whenever a secret cannot be found."""
    pass

class HTTPUnexpectedResponse(Exception):
    """Raise this exception whenever an unexpected response is encountered."""
    pass

class HTTPBadStatus(Exception):
    """Raise this exception whenever an unexpected HTTP status code is encountered."""
    def __init__(self, expected: int, actual: int) -> None:
        message = f"Expected status code {expected}, got {actual}."
        super().__init__(message)
