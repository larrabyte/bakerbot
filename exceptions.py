import typing as t
import http.client

class SecretNotFound(Exception):
    """Raised whenever a secret cannot be found."""
    pass

class HTTPUnexpected(Exception):
    """Raised whenever an unexpected response is encountered."""
    def __init__(self, status: int, error: t.Optional[str]=None) -> None:
        message = error or f"Endpoint returned HTTP {status} {http.client.responses[status]}."
        super().__init__(message)
