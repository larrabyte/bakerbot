import exceptions
import model

import typing as t
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

class Chapter:
    """A class that represents Mangadex's `Chapter` object."""
    def __init__(self, data: dict) -> None:
        self.identifier: str = data["id"]
        self.title: str = data["attributes"]["title"]
        self.volume: t.Optional[str] = data["attributes"]["volume"]
        self.chapter: t.Optional[str] = data["attributes"]["chapter"]
        self.language: str = data["attributes"]["translatedLanguage"]
        self.hash: str = data["attributes"]["hash"]
        self.data: t.List[str] = data["attributes"]["data"]
        self.data_saver: t.List[str] = data["attributes"]["dataSaver"]

        # WTFMD: `uploader` does not exist here???
        # self.uploader: str = data["attributes"]["uploader"]

        self.external_url: t.Optional[str] = data["attributes"]["externalUrl"]
        self.version: int = data["attributes"]["version"]
        self.created_at: int = data["attributes"]["createdAt"]
        self.updated_at: int = data["attributes"]["updatedAt"]
        self.publish_at: int = data["attributes"]["publishAt"]

        self.relationships: t.List[Relationship] = []
        for relationship in data["relationships"]:
            ship = Relationship(relationship)
            self.relationships.append(ship)

        self.base_url: t.Optional[str] = None

    async def base(self) -> None:
        """Populates the base URL attribute for this chapter."""
        data = await Backend.get(f"at-home/server/{self.identifier}")
        self.base_url = data["baseUrl"]

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

        self.volumes: t.Optional[dict] = None
        self.chapters: t.Optional[t.List[Chapter]] = None

    def search_relationships(self, identifier: str) -> t.List[Relationship]:
        """Searches the list of relationships for `identifier`."""
        return [r for r in self.relationships if r.type == identifier]

    def volume_count(self) -> int:
        """Returns the number of volumes in this manga."""
        if self.volumes is None:
            raise exceptions.NoInformation("Aggregate not available.")

        count = len(self.volumes.values())
        if "none" in self.volumes.values():
            count -= 1

        return count

    def chapter_count(self) -> int:
        """Returns the number of chapters in this manga."""
        if self.volumes is None:
            raise exceptions.NoInformation("Aggregate not available.")

        return sum(volume["count"] for volume in self.volumes.values())

    async def cover(self) -> t.Optional[str]:
        """Returns the cover for this manga."""
        if (covers := self.search_relationships("cover_art")):
            # Just pick the first cover for now.
            data = await Backend.get(f"cover/{covers[0].identifier}")
            filename = data["data"]["attributes"]["fileName"]
            return f"{Backend.data}/covers/{self.identifier}/{filename}"

        return None

    async def author(self) -> t.Optional[str]:
        """Returns the author for this manga."""
        if (authors := self.search_relationships("author")):
            # Just pick the first author for now.
            data = await Backend.get(f"author/{authors[0].identifier}")
            return data["data"]["attributes"]["name"]

        return None

    async def aggregate(self, language: str) -> None:
        """Populates this manga's volume information."""
        parameters = {"translatedLanguage[]": language}
        data = await Backend.get(f"manga/{self.identifier}/aggregate", params=parameters)
        self.volumes = data["volumes"]

    async def feed(self, language: str) -> None:
        """Populates this manga's chapter information."""
        count = self.chapter_count()
        self.chapters = []
        offset = 0

        while count > 0:
            limit = min(count, 500)
            parameters = {"limit": limit, "offset": offset, "translatedLanguage[]": language, "order[chapter]": "asc"}
            data = await Backend.get(f"manga/{self.identifier}/feed", params=parameters)
            chapters = [Chapter(m) for m in data["data"]]
            self.chapters.extend(chapters)
            count -= limit
            offset += limit

class Backend:
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        """Initialises an instance of `Backend` using objects from `bot`."""
        cls.base = "https://api.mangadex.org"
        cls.data = "https://uploads.mangadex.org"
        cls.client = "https://mangadex.org"
        cls.session = bot.session

    @classmethod
    async def get(cls, endpoint: str, **kwargs: dict) -> dict:
        """Sends a HTTP GET request to the base Mangadex API."""
        async with cls.session.get(f"{cls.base}/{endpoint}", **kwargs) as response:
            data = await response.read()

            if response.status != http.HTTPStatus.OK:
                try: formatted = ujson.loads(data)
                except ValueError: formatted = {}
                error = str(formatted.get("errors", None))
                raise exceptions.HTTPUnexpected(response.status, error)

            return ujson.loads(data)

    @classmethod
    async def manga(cls, title: str) -> Manga:
        """Returns a `Manga` object by searching the API."""
        parameters = {"limit": 1, "title": title}
        data = await cls.get("manga", params=parameters)

        if data["result"] != "ok":
            errored = data["data"][0]
            errors = errored.get("errors", [])
            readable = ", ".join(errors) or None
            raise exceptions.HTTPUnexpected(http.HTTPStatus.OK, readable)

        data = data["data"][0]
        return Manga(data)

    @classmethod
    async def search(cls, title: str, maximum: int) -> t.List[Manga]:
        """Returns a `Manga` object or list of `Manga` objects up to `maximum` in length."""
        if not 1 <= maximum <= 100:
            raise ValueError("Maximum must be between 1 and 100.")

        parameters = {"limit": maximum, "title": title}
        data = await cls.get("manga", params=parameters)
        return [Manga(m) for m in data["data"]]

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
