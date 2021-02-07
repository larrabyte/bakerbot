import typing as t
import aiohttp

class Word:
    def __init__(self, metadata: dict) -> None:
        self.slug = metadata["slug"]
        self.tags = metadata["tags"]
        self.jlpt = metadata["jlpt"]

        # Word sense (definition, parts of speech, other info).
        senses = metadata["senses"][0]
        self.meanings = senses["english_definitions"]
        self.speech = senses["parts_of_speech"]
        self.info = senses["info"]

        # This is where the optional entries come in.
        furigana = metadata["japanese"][0]
        self.kana = furigana.get("reading", "")
        self.written = furigana.get("word", self.kana)

    @property
    def types(self) -> str:
        # Return the parts of speech this word is capable of acting as.
        return ", ".join(self.speech)

    @property
    def definitions(self) -> str:
        # Return the meanings of this word in a comma-separated list.
        return ", ".join(self.meanings)

class Jisho:
    @classmethod
    async def setup(cls, session: aiohttp.ClientSession) -> None:
        cls.base = "https://jisho.org/api/v1/"
        cls.session = session

    @classmethod
    async def request(cls, path: str) -> t.Optional[dict]:
        # Make a HTTP GET request to the Mangadex API.
        async with cls.session.get(f"{cls.base}{path}") as resp:
            data = await resp.json()

            if data["meta"]["status"] != 200:
                return None

            return data["data"]

    @classmethod
    async def search(self, query: str) -> t.Optional[dict]:
        # Search the Jisho API for a specific query.
        if (response := await Jisho.request(f"search/words?keyword={query}")) is not None:
            return [Word(words) for words in response[:9]]

        return None
