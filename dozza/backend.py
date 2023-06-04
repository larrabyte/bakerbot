import dozza.types as types

import dataclasses
import aiohttp
import typing

class Error(Exception):
    """Something unexpected happened on sv443's end."""
    def __init__(self, reason: str):
        self.reason = reason

    def __str__(self) -> str:
        return self.reason

@dataclasses.dataclass
class Joke:
    """Holds funny stuff."""
    quip: str
    followup: str | None

async def request(session: aiohttp.ClientSession) -> types.Reply:
    """Request a joke from the sv443 JokeAPI."""
    async with session.get("https://v2.jokeapi.dev/joke/Any") as response:
        payload = typing.cast(types.Payload, await response.json())

        if payload["error"]:
            failure = typing.cast(types.Error, payload)
            error = failure["message"]
            raise Error(error)

        return typing.cast(types.Reply, payload)

async def funny(session: aiohttp.ClientSession) -> Joke:
    """Get a fucking joke."""
    response = await request(session)

    # This is valid since the response must either be a single or compound joke.
    quip = typing.cast(str, response.get("joke") or response.get("setup"))
    followup = typing.cast(str | None, response.get("delivery"))

    return Joke(quip, followup)
