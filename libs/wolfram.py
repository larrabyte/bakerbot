from yarl import URL

import typing as t
import aiohttp
import hashlib
import urllib
import json

class Query:
    def __init__(self, link: str, results: dict) -> None:
        self.success = results["success"]
        self.error = results["error"]
        self.return_time = results["timing"]
        self.process_time = results["parsetiming"]
        self.link = link

        # Attributes that may not necessarily exist.
        self.rawtips = results.get("tips", None)
        self.pods = results.get("pods", None)

    @property
    def tips(self) -> t.List[str]:
        # Return a list of tips using self.rawtips.
        if self.rawtips is None:
            return []

        if isinstance(self.rawtips, list):
            return [f"-> {tip['text']}." for tip in self.rawtips]

        if isinstance(self.rawtips, dict):
            return [f"-> {self.rawtips['text']}."]

class Wolfram:
    @classmethod
    async def setup(cls, session: aiohttp.ClientSession) -> None:
        cls.base = "https://api.wolframalpha.com/v2/"
        cls.id = "3H4296-5YPAGQUJK7"
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
            "podstate": "Step-by-step+solution",
            "reinterpret": "true"
        }

        queries.update(kwargs) # Add any extra kwargs available and sort.
        queries = {k: v for k, v in sorted(queries.items())}

        # Calculate the MD5 signature for this specific query.
        queries.update({"sig": Wolfram.digest(queries)})
        encoded = urllib.parse.urlencode(queries, quote_via=Wolfram.nothing)
        path = f"query.jsp?{encoded}"

        if (data := await Wolfram.request(path)) is not None:
            return Query(link=f"{cls.base}{path}", results=data)

        return None
