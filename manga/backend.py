import manga.types as types

import dataclasses
import aiohttp
import asyncio
import typing
import json

class Error(Exception):
    """Mangadex returned an error."""
    def __init__(self, reason: str):
        self.reason = reason

    def __str__(self):
        return self.reason

@dataclasses.dataclass
class Relationship:
    """Defines the relationship of a person to a manga."""
    id: str
    type: str

@dataclasses.dataclass
class Chapter:
    """A manga chapter."""
    id: str
    volume: str | None
    chapter: str

    async def pages(self, session: aiohttp.ClientSession) -> list[str]:
        """Request the pages for this chapter."""
        response = await request(session, f"https://api.mangadex.org/at-home/server/{self.id}")
        metadata = typing.cast(types.CDNResponse, response)

        return [
            f"{metadata['baseUrl']}/data/{metadata['chapter']['hash']}/{image}"
            for image in metadata["chapter"]["data"]
        ]

@dataclasses.dataclass
class Manga:
    """A manga."""
    id: str
    tags: list[str]
    relationships: list[Relationship]
    title: str | None
    description: str | None
    demographic: str | None
    status: str | None
    year: int | None

    async def authors(self, session: aiohttp.ClientSession) -> list[str]:
        """Request the names of the authors."""
        callbacks = [
            request(session, f"https://api.mangadex.org/author/{rel.id}")
            for rel in self.relationships if rel.type == "author"
        ]

        results = typing.cast(list[types.AuthorResponse], await asyncio.gather(*callbacks))
        return [result["data"]["attributes"]["name"] for result in results]

    async def chapters(self, session: aiohttp.ClientSession) -> list[Chapter]:
        """Request the list of chapters."""
        response = await request(
            session,
            f"https://api.mangadex.org/manga/{self.id}/aggregate",
            params={"translatedLanguage[]": "en"}
        )

        aggregate = typing.cast(types.AggregateResponse, response)

        return [
            Chapter(chapter["id"], vol if (vol := volume["volume"]) != "none" else None, chapter["chapter"])
            for volume in (dict() if isinstance(aggregate["volumes"], list) else aggregate["volumes"]).values()
            for chapter in (dict() if isinstance(volume["chapters"], list) else volume["chapters"]).values()
        ]

async def request(session: aiohttp.ClientSession, url: str, **kwargs) -> types.Payload:
    """Send a request to the Mangadex API."""
    async with session.get(url, **kwargs) as response:
        data = await response.read()
        payload = typing.cast(types.Payload, json.loads(data))

        if payload["result"] == "error":
            failure = typing.cast(types.ErrorResponse, payload)
            raise ExceptionGroup("", [Error(error["detail"]) for error in failure["errors"]])

        return payload

async def search(session: aiohttp.ClientSession, title: str) -> list[Manga]:
    """Search for a manga."""
    payload = await request(
        session,
        "https://api.mangadex.org/manga",
        params={"title": title}
    )

    result = typing.cast(types.MangaList, payload)

    return [
        Manga(
            manga["id"],
            [tag["attributes"]["name"]["en"] for tag in manga["attributes"]["tags"] if "en" in tag["attributes"]["name"]],
            [Relationship(rel["id"], rel["type"]) for rel in manga["relationships"]],
            manga["attributes"]["title"].get("en"),
            manga["attributes"]["description"].get("en"),
            audience.capitalize() if (audience := manga["attributes"]["publicationDemographic"]) is not None else None,
            status.capitalize() if (status := manga["attributes"]["status"]) is not None else None,
            manga["attributes"]["year"],
        )

        for manga in result["data"]
    ]
