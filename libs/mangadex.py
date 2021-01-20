import typing as t
import aiohttp

class Ratings:
    def __init__(self, metadata: dict) -> None:
        self.bayesian = metadata["bayesian"]
        self.mean = metadata["mean"]
        self.users = metadata["users"]

class Chapter:
    def __init__(self, metadata: dict) -> None:
        self.id = metadata["id"]
        self.hash = metadata["hash"]
        self.volume = metadata["volume"]
        self.chapter = metadata["chapter"]
        self.title = metadata["title"]

    def __str__(self) -> str:
        # Return the title of this chapter.
        volume = f"Vol. {self.volume}" if self.volume else ""
        chapter = f"Ch. {self.chapter}" if self.chapter else ""
        title = f"- {self.title}" if self.title else ""

        return f"{volume} {chapter} {title}"

    async def images(self) -> t.AsyncGenerator[str, None]:
        # Return a list of URLs pointing to the images in this chapter.
        metadata = await Mangadex.request(f"chapter/{self.id}")
        server = metadata.get("serverFallback", metadata["server"])
        pages = metadata["pages"]

        for page in pages:
            yield f"{server}/{self.hash}/{page}"

class Manga:
    def __init__(self, metadata: dict, chapters: dict, lang: str) -> None:
        self.id = metadata["id"]
        self.title = metadata["title"]
        self.authorlist = metadata["author"]
        self.views = metadata["views"]
        self.follows = metadata["follows"]
        self.cover = metadata["mainCover"]

        # Custom classes and/or processing required.
        self.ratings = Ratings(metadata["rating"])
        self.taglist = [Mangadex.tags[str(tag)] for tag in metadata["tags"]]
        self.chapters = [Chapter(data) for data in chapters["chapters"] if data["language"] == lang]
        self.chapters.sort(key=lambda c: float(c.chapter) if c.chapter else float(0))

    @property
    def authors(self) -> str:
        # Return a string of authors.
        return ", ".join(self.authorlist)

    @property
    def tags(self) -> str:
        # Return a string of formatted tags.
        formatted = "`Unknown`" if not self.taglist else ""
        for index, tag in enumerate(self.taglist, 1):
            formatted += f"`{tag['name']}` "
            if index % 3 == 0: formatted += "\n"

        return formatted

class Mangadex:
    @classmethod
    async def setup(cls, session: aiohttp.ClientSession) -> None:
        cls.base = "https://mangadex.org/api/v2/"
        cls.session = session
        cls.tags = await Mangadex.request("tag")

    @classmethod
    async def request(cls, path: str) -> t.Optional[dict]:
        # Make a HTTP GET request to the Mangadex API.
        async with cls.session.get(f"{cls.base}{path}") as resp:
            if resp.status != 200:
                return None

            data = await resp.json()
            return data["data"]

    @classmethod
    async def create(cls, id: int, lang: str) -> t.Optional[Manga]:
        # Create and return a Manga object using the ID and langauge passed in.
        if (metadata := await Mangadex.request(f"manga/{id}")) is not None:
            chapters = await Mangadex.request(f"manga/{id}/chapters")
            return Manga(metadata=metadata, chapters=chapters, lang=lang)

        return None
