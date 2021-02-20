import typing as t
import aiohttp
import html

class Page:
    def __init__(self, metadata: dict) -> None:
        self.title = metadata["title"]
        self.pageid = metadata["pageid"]
        self.extract = metadata["extract"]

        # Thumbnail data.
        thumb = metadata.get("thumbnail", {})
        self.thumbnail = thumb.get("source", None)

class Results:
    def __init__(self, metadata: dict) -> None:
        self.title = metadata["title"]
        self.pageid = metadata["pageid"]
        self.snippet = metadata["snippet"]

    @property
    def summary(self) -> str:
        snipped = self.snippet.replace("<span class=\"searchmatch\">", "").replace("</span>", "")
        return html.unescape(f"{snipped}...")

class Wikipedia:
    @classmethod
    async def setup(cls, session: aiohttp.ClientSession) -> None:
        cls.base = "https://en.wikipedia.org/w/"
        cls.session = session

    @classmethod
    async def request(cls, path: str, params: t.Optional[dict]) -> t.Optional[dict]:
        # Make a HTTP GET request to Wikipedia's API.
        async with cls.session.get(f"{cls.base}{path}", params=params) as resp:
            data = await resp.json()

            if resp.status != 200:
                return None

            return data["query"]

    @classmethod
    async def search(cls, query: str) -> t.Optional[dict]:
        # Search the Wikipedia API for a page.
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 9,
            "format": "json"
        }

        if (response := await Wikipedia.request(path="api.php", params=params)) is not None:
            return [Results(result) for result in response["search"]]

        return None

    @classmethod
    async def article(cls, pageid: int) -> t.Optional[dict]:
        # Request an article from the Wikipedia API.
        params = {
            "action": "query",
            "pageids": pageid,
            "prop": "extracts|pageimages",
            "exchars": 1000,
            "explaintext": "true",
            "piprop": "thumbnail",
            "pithumbsize": 500,
            "format": "json"
        }

        if (response := await Wikipedia.request(path="api.php", params=params)) is not None:
            return Page(response["pages"][f"{pageid}"])

        return None
