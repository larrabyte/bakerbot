import keychain
import aiohttp
import typing
import re

class MediaFormat(typing.TypedDict):
    """The format of a Media Format object."""
    url: str
    dims: list[int]
    duration: float
    size: int

class Response(typing.TypedDict):
    """The format of an API Response object."""
    created: float
    hasaudio: bool
    id: str
    media_formats: dict[str, MediaFormat]
    tags: list[str]
    title: str
    content_description: str
    itemurl: str
    hascaption: bool
    flags: str
    bg_color: str
    url: str

class Payload(typing.TypedDict):
    """The format of the payload from the post endpoint."""
    results: list[Response]

async def raw(session: aiohttp.ClientSession, url: str) -> str | None:
    """Convert a Tenor item URL into a raw GIF URL."""
    match = re.match(r"^https://tenor\.com/view/(-?([A-Za-z0-9]+))+$", url)

    if match is None:
        return None

    params = {
        "key": keychain.TENOR_KEY,
        "ids": match.group(2)
    }

    async with session.get("https://tenor.googleapis.com/v2/posts", params=params) as response:
        payload = typing.cast(Payload, await response.json())
        format = payload["results"][0]["media_formats"].get("gif", None)
        return format["url"] if format is not None else None
