import typing as t
import aiohttp

class Word:
    def __init__(self, metadata: dict) -> None:
        self.slug = metadata["slug"]
        self.tags = metadata["tags"]
        self.jlpt = metadata["jlpt"]

        # Get the pronunciation and writing of the word.
        furigana = metadata["japanese"][0]
        self.kana = furigana.get("reading", "")
        self.written = furigana.get("word", self.kana)

        # Word senses (definition, parts of speech, readings, etc).
        self.meanings = set()
        self.speech = set()

        for sense in metadata["senses"]:
            self.meanings.update(sense["english_definitions"])
            self.speech.update(sense["parts_of_speech"])

    @property
    def types(self) -> str:
        # Return the parts of speech this word is capable of acting as.
        return ", ".join(self.speech)

    @property
    def definitions(self) -> str:
        # Return the meanings of this word in a comma-separated list.
        meanings = ", ".join(self.meanings)
        if len(meanings) > 60:
            return f"{meanings[0:60]}..."

        return meanings

class Jisho:
    @classmethod
    async def setup(cls, session: aiohttp.ClientSession) -> None:
        cls.base = "https://jisho.org/api/v1/"
        cls.session = session

    @classmethod
    async def request(cls, path: str) -> t.Optional[dict]:
        # Make a HTTP GET request to Jisho's API.
        async with cls.session.get(f"{cls.base}{path}") as resp:
            data = await resp.json()

            if data["meta"]["status"] != 200:
                return None

            return data["data"]

    @classmethod
    async def search(cls, query: str) -> t.Optional[dict]:
        # Search the Jisho API for a specific query.
        if (response := await Jisho.request(f"search/words?keyword={query}")) is not None:
            return [Word(words) for words in response[:9]]

        return None
