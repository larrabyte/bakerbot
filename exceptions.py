import model

import http.client

class HTTPUnexpected(Exception):
    """Raised whenever an unexpected response is encountered."""
    def __init__(self, status: int, error: str | None = None) -> None:
        message = error or f"Endpoint returned HTTP {status} {http.client.responses[status]}."
        super().__init__(message)

def setup(bot: model.Bakerbot) -> None:
    pass
