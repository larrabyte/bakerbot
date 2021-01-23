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
        queries["input"] = urllib.parse.quote_plus(queries["input"])
        for k, v in queries.items(): salt += f"{k}{v}"

        # Undo the canonisation done to the input entry and hash.
        signature = hashlib.md5(salt.encode(encoding="utf-8"))
        queries["input"] = urllib.parse.unquote_plus(queries["input"])
        return signature.hexdigest().upper()

    @classmethod
    async def request(cls, path: str) -> t.Optional[dict]:
        # Make a HTTP GET request to WolframAlpha's API.
        async with cls.session.get(URL(f"{cls.base}{path}", encoded=True)) as resp:
            data = await resp.read()
            data = json.loads(data)

            if resp.status != 200:
                return None

            return data["queryresult"]

    @classmethod
    async def query(cls, userinput: str) -> t.Optional[Query]:
        # Handle the setup for sending a query off to the API.
        # This dictionary must be sorted by the key's alphabetical order!
        queries = {
            "appid": cls.id,
            "input": userinput,
            "output": "json",
            "podstate": "Step-by-step",
            "reinterpret": "true"
        }

        # Calculate the MD5 signature for this specific query.
        queries.update({"sig": Wolfram.digest(queries)})
        path = f"query.jsp?{urllib.parse.urlencode(queries)}"

        if (data := await Wolfram.request(path)) is not None:
            return Query(link=f"{cls.base}{path}", results=data)

        return None
