import model

import aiohttp
import urllib
import ujson
import yarl

class Backend:
    """The Mangadex API wrapper."""
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session

    def mangaUUID(self, manga: dict) -> str:
        """Returns the manga UUID from a given manga object."""
        return manga["data"]["id"]

    def coverUUID(self, manga: dict) -> str:
        """Returns the cover UUID from a given manga object."""
        return next(entry["id"] for entry in manga["relationships"] if entry["type"] == "cover_art")

    async def request(self, path: str) -> dict:
        """Sends a HTTP GET request to the Mangadex API."""
        url = yarl.URL(path, encoded=True)

        async with self.session.get(url) as resp:
            data = await resp.read()
            data = data.decode("utf-8")
            return ujson.loads(data)

    async def cover(self, manga: str, cover: str) -> str:
        """Returns the URL for a cover given manga and cover UUIDs."""
        data = await self.request(f"https://api.mangadex.org/cover/{cover}")
        filename = data["data"]["attributes"]["fileName"]
        return f"https://uploads.mangadex.org/covers/{manga}/{filename}"

    async def server(self, uuid: str) -> str:
        """Returns a valid MD@H server for a given manga UUID."""
        path = f"https://api.mangadex.org/at-home/server/{uuid}"
        results = await self.request(path)
        return results["baseUrl"]

    async def search(self, title: str, maximum: int) -> dict:
        """Searches for a manga."""
        params = {"title": title, "limit": maximum}
        encoder = urllib.parse.quote_plus
        params = urllib.parse.urlencode(params, quote_via=encoder)

        path = f"https://api.mangadex.org/manga?{params}"
        results = await self.request(path)
        return results

    async def aggregate(self, uuid: str) -> dict:
        """Returns an aggregate of volumes/chapters for a manga using a given UUID."""
        path = f"https://api.mangadex.org/manga/{uuid}/aggregate?translatedLanguage[]=en"
        results = await self.request(path)
        return results

    async def feed(self, uuid: str, limit: int, offset: int) -> dict:
        """Returns the feed of a manga given a UUID, limit and offset."""
        path = f"https://api.mangadex.org/manga/{uuid}/feed?limit={limit}&offset={offset}&translatedLanguage[]=en&order[chapter]=asc"
        results = await self.request(path)
        return results

def setup(bot: model.Bakerbot) -> None:
    pass
