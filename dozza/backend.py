from dozza import types

import aiohttp
import typing
import json

async def request(session: aiohttp.ClientSession) -> types.Single | types.Compound:
    """Request a joke from the sv443 JokeAPI."""
    async with session.get("https://v2.jokeapi.dev/joke/Any") as response:
        data = await response.read()
        bundle = json.loads(data)

        # The bundle will be an instance of types.Payload.
        # If it also has an error field set to true,
        # then it's an instance of types.Error.
        if bundle["error"]:
            raise RuntimeError(bundle["message"])

        return bundle

async def funny(session: aiohttp.ClientSession) -> types.Joke:
    """Get a fucking joke."""
    bundle = await request(session)
    quip = bundle.get("joke") or bundle.get("setup")
    followup = bundle.get("delivery")

    return types.Joke(quip, followup) # type: ignore
