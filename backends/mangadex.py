import exceptions
import model

import typing as t
import aiohttp
import ujson
import http

class Relationship:
    """A class that represents Mangadex's `Relationship` object."""
    def __init__(self, data: dict) -> None:
        self.identifier: str = data["id"]
        self.type: str = data["type"]
        self.attributes: t.Optional[t.Dict] = data.get("attributes", None)

class Tag:
    """A class that represents Mangadex's `Tag` object."""
    def __init__(self, data: dict) -> None:
        self.identifier: str = data["id"]
        self.name: str = data["attributes"]["name"]["en"]

        # WTFMD: `description` is documented to be of type `LocalizedString`, but is a list.
        # self.description: t.List[str] = data["attributes"]["description"]

        self.group: str = data["attributes"]["group"]
        self.version: int = data["attributes"]["version"]

        self.relationships: t.List[Relationship] = []
        for relationship in data["relationships"]:
            ship = Relationship(relationship)
            self.relationships.append(ship)

class Manga:
    """A class that represents Mangadex's `Manga` object."""
    def __init__(self, data: dict) -> None:
        self.identifier: str = data["id"]
        self.title: str = data["attributes"]["title"]["en"]

        self.alt_titles: t.List[str] = []
        for titles in data["attributes"]["altTitles"]:
            titles = list(titles.values())
            self.alt_titles.extend(titles)

        self.description: str = data["attributes"]["description"]["en"]

        # WTFMD: `isLocked` was removed from the API, but it's still in the docs.
        # self.is_locked: bool = data["attributes"]["isLocked"]

        self.links: t.Dict[str, str] = data["attributes"]["links"]
        self.original_language: str = data["attributes"]["originalLanguage"]
        self.last_volume: t.Optional[str] = data["attributes"]["lastVolume"]
        self.last_chapter: t.Optional[str] = data["attributes"]["lastChapter"]
        self.demographic: t.Optional[str] = data["attributes"]["publicationDemographic"]
        self.status: t.Optional[str] = data["attributes"]["status"]
        self.year: t.Optional[int] = data["attributes"]["year"]
        self.content_rating: str = data["attributes"]["contentRating"]

        self.tags: t.List[Tag] = []
        for tag in data["attributes"]["tags"]:
            taggified = Tag(tag)
            self.tags.append(taggified)

        self.version: int = data["attributes"]["version"]
        self.created_at: str = data["attributes"]["createdAt"]
        self.updated_at: str = data["attributes"]["updatedAt"]

        self.relationships: t.List[Relationship] = []
        for relationship in data["relationships"]:
            ship = Relationship(relationship)
            self.relationships.append(ship)

    def search_relationships(self, identifier: str) -> t.List[Relationship]:
        """Searches the list of relationships for `identifier`."""
        return [r for r in self.relationships if r.type == identifier]

    async def cover(self) -> t.Optional[str]:
        """Returns the cover for this manga."""
        if (covers := self.search_relationships("cover_art")):
            # Just pick the first cover for now.
            data = await Backend.request(f"cover/{covers[0].identifier}")
            filename = data["data"]["attributes"]["fileName"]
            return f"{Backend.data}/covers/{self.identifier}/{filename}"

        return None

    async def author(self) -> t.Optional[str]:
        """Returns the author for this manga."""
        if (authors := self.search_relationships("author")):
            # Just pick the first author for now.
            data = await Backend.request(f"author/{authors[0].identifier}")
            return data["data"]["attributes"]["name"]

class Backend:
    """The Mangadex API wrapper."""
    base = "https://api.mangadex.org"
    data = "https://uploads.mangadex.org"
    client = "https://mangadex.org"
    session: aiohttp.ClientSession

    @classmethod
    async def request(cls, endpoint: str, parameters: dict={}) -> dict:
        """Sends a HTTP GET request to the base Mangadex API."""
        async with cls.session.get(f"{cls.base}/{endpoint}", params=parameters) as response:
            data = await response.read()

            if response.status != http.HTTPStatus.OK:
                try: formatted = ujson.loads(data)
                except ValueError: formatted = {}
                error = str(formatted.get("errors", None))
                raise exceptions.HTTPUnexpected(response.status, error)

            return ujson.loads(data)

    @classmethod
    async def search(cls, title: str, maximum: int) -> t.Union[Manga, t.List[Manga]]:
        """Returns a `Manga` object or list of `Manga` objects up to `maximum` in length."""
        if not 1 <= maximum <= 100:
            raise ValueError("Maximum must be between 1 and 100.")

        parameters = {"limit": maximum, "title": title}
        data = await cls.request("manga", parameters)

        if maximum == 1:
            if data["results"][0]["result"] != "ok":
                errored = data["results"][0]
                errors = errored.get("errors", [])
                readable = ", ".join(errors) or None
                raise exceptions.HTTPUnexpected(http.HTTPStatus.OK, readable)

            data = data["results"][0]["data"]
            return Manga(data)

        # If the maximum is > 1, then just return the manga that were successful.
        return [Manga(m) for m in data["results"] if m["result"] == "ok"]

def setup(bot: model.Bakerbot) -> None:
    Backend.session = bot.session
