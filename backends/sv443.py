from functools import reduce
import exceptions
import model

import typing
import ujson
import http

class Response(typing.TypedDict, total=False):
    """Represents a response from sv443's joke API."""
    formatVersion: int
    category: str
    type: str

    joke: str | None      # Only present if `type` is "single".
    setup: str | None     # Only present if `type` is "twopart".
    delivery: str | None  # Only present if `type` is "twopart".

    flags: dict[str, bool]
    lang: str

class Backend:
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        cls.base = "https://v2.jokeapi.dev"
        cls.session = bot.session

    @classmethod
    async def get(cls, endpoint: str, **kwargs: dict) -> dict:
        """Send a HTTP GET request to sv443's joke API."""
        async with cls.session.get(f"{cls.base}/{endpoint}", **kwargs) as response:
            data = await response.read()

            if response.status == http.HTTPStatus.TOO_MANY_REQUESTS:
                raise TooManyRequests
            elif response.status != http.HTTPStatus.OK:
                raise exceptions.HTTPUnexpected(response.status)

            return ujson.loads(data)

    @classmethod
    async def joke(cls) -> Response:
        """Retrieve a joke."""
        return await cls.get("joke/Any")

class TooManyRequests(Exception):
    """Raised when too many requests are being sent at once (docs say >120/minute)."""
    pass

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
