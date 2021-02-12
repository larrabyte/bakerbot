from libs.utilities import Regexes
from yarl import URL

import typing as t
import aiohttp
import secrets
import hashlib
import urllib
import json

class Subpod:
    def __init__(self, title: str, data: object) -> None:
        self.title = title
        self.data = data

    @property
    def plaintext(self) -> t.Optional[str]:
        # Returns the plaintext for this subpod if available.
        if (text := self.data.get("plaintext", "")) != "":
            if len(text) > 1024:
                return f"{text[0:1021]}..."

            return text

        return None

    @property
    def image(self) -> t.Optional[str]:
        # Returns the image for this subpod if available.
        if (image := self.data.get("img"), None) is not None:
            return image["src"]

        return None

class Pod:
    def __init__(self, data: dict) -> None:
        self.title = data["title"]
        self.scanner = data["scanner"]
        self.position = data["position"]
        self.error = data["error"]

        self.subpods = [Subpod(title=subpod["title"] or self.title, data=subpod) for subpod in data["subpods"]]

class Query:
    def __init__(self, link: str, results: dict) -> None:
        self.success = results["success"]
        self.timing = results["timing"]

        tips = results.get("tips", [])
        self.tips = [tips["text"]] if isinstance(tips, dict) else [tip["text"] for tip in tips]

        self.error = True if isinstance(results["error"], dict) else False
        self.errmsg = results["error"]["msg"] if self.error else ""
        self.pods = [Pod(pod) for pod in results.get("pods", [])]
        self.link = link

    @property
    def formattedtips(self) -> str:
        # Return a formatted string of tips.
        raw = "\n".join([f"-> {tip}." for tip in self.tips])
        return Regexes.escapemd(raw)

class Wolfram:
    @classmethod
    async def setup(cls, session: aiohttp.ClientSession, signing: bool) -> None:
        cls.base = "https://api.wolframalpha.com/v2/"
        cls.id = secrets.wakey
        cls.signing = signing
        cls.session = session

    @staticmethod
    def digest(queries: dict) -> str:
        # Create a digest for a dictionary of queries.
        salt = "vFdeaRwBTVqdc5CL"
        for k, v in queries.items(): salt += f"{k}{v}"

        # Undo the canonisation done to the input entry and hash.
        signature = hashlib.md5(salt.encode(encoding="utf-8"))
        return signature.hexdigest().upper()

    @staticmethod
    def nothing(string: str, safe: str, encoding: str=None, errors: object=None) -> str:
        # Skip URL encoding, don't do anything.
        return string

    @classmethod
    async def request(cls, path: str) -> t.Optional[dict]:
        # Make a HTTP GET request to WolframAlpha's API.
        async with cls.session.get(URL(f"{cls.base}{path}", encoded=True)) as resp:
            if resp.status != 200:
                return None

            data = await resp.read()
            data = json.loads(data)
            return data["queryresult"]

    @classmethod
    async def query(cls, query: str, formats: str, **kwargs) -> t.Optional[Query]:
        queries = {
            "appid": cls.id,
            "format": formats,
            "input": urllib.parse.quote_plus(query),
            "output": "json",
            "reinterpret": "true"
        }

        queries.update(kwargs) # Add any extra kwargs available and sort.
        queries = {k: v for k, v in sorted(queries.items())}

        # Calculate the MD5 signature for this specific query.
        if cls.signing: queries.update({"sig": Wolfram.digest(queries)})
        encoded = urllib.parse.urlencode(queries, quote_via=Wolfram.nothing)
        path = f"query.jsp?{encoded}"

        if (data := await Wolfram.request(path)) is not None:
            return Query(link=f"{cls.base}{path}", results=data)

        return None
