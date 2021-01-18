import typing as t
import operator
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

    async def images(self) -> t.AsyncGenerator[str, None]:
        # Return a list of URLs pointing to the images in this chapter.
        metadata = await Mangadex.request(f"/chapter/{self.id}")
        server = metadata.get("serverFallback", metadata["server"])[:-1]
        pages = metadata["pages"]

        for page in pages:
            yield f"{server}/{self.hash}/{page}"

    def sort_function(self) -> float:
        # Used by list.sort() to sort chapters.
        if self.chapter:
            return float(self.chapter)

        return float(0)

    def __str__(self) -> str:
        # Return the title of this chapter.
        volume = f"Vol. {self.volume}" if self.volume else ""
        chapter = f"Ch. {self.chapter}" if self.chapter else ""
        title = f"- {self.title}" if self.title else ""

        return f"{volume} {chapter} {title}"

class Manga:
    @classmethod
    async def create(cls, id: int, lang: str) -> object:
        # Use this method to create a Manga object using data from the Mangadex API.
        metadata = await Mangadex.request(f"/manga/{id}")
        if metadata is None: return None
        instance = Manga()

        # Request a list of chapters from the API and cache them in a list.
        chapters = await Mangadex.request(f"/manga/{id}/chapters")
        instance.chapters = [Chapter(data) for data in chapters["chapters"] if data["language"] == lang]
        instance.chapters.sort(key=operator.methodcaller("sort_function"))

        # Set the remaining properties from the metadata.
        instance.id = metadata["id"]
        instance.title = metadata["title"]
        instance.authorlist = metadata["author"]
        instance.taglist = [Mangadex.tags[tag] for tag in metadata["tags"]]
        instance.ratings = Ratings(metadata["rating"])
        instance.views = metadata["views"]
        instance.follows = metadata["follows"]
        instance.cover = metadata["mainCover"]
        return instance

    @property
    def authors(self) -> str:
        return ", ".join(self.authorlist)

    @property
    def tags(self) -> str:
        formatted = "`Unknown`" if not self.taglist else ""
        for index, tag in enumerate(self.taglist, 1):
            name = tag["name"]
            formatted += f"`{name}` "
            if index % 3 == 0:
                formatted += "\n"

        return formatted

class Mangadex:
    @classmethod
    async def create(cls) -> None:
        cls.client = aiohttp.ClientSession()
        cls.base = "https://mangadex.org/api/v2"

        # Convert keys to integers to make accessing easier.
        tagdict = await Mangadex.request("/tag")
        cls.tags = {int(k): v for k, v in tagdict.items()}

    @classmethod
    async def request(cls, path: str) -> t.Optional[dict]:
        # Make a HTTP GET request to the Mangadex API.
        async with cls.client.get(f"{cls.base}{path}") as resp:
            if resp.status != 200:
                return None

            data = await resp.json()
            return data["data"]
