import exceptions

import hashlib
import aiohttp
import urllib
import ujson
import yarl

class Backend:
    """The WolframAlpha API wrapper."""
    def __init__(self, secrets: dict, session: aiohttp.ClientSession) -> None:
        self.id = secrets.get("wolfram-id", None)
        self.salt = secrets.get("wolfram-salt", None)
        self.hashing = secrets.get("wolfram-hash", False)
        self.v2base = "https://api.wolframalpha.com/v2"
        self.session = session

    def valid(self, results: dict) -> bool:
        """Checks whether WolframAlpha gave a successful response."""
        success = results.get("success", False)
        error = results.get("error", True)
        return success and not error

    def digest(self, results: dict) -> str:
        """Returns an MD5 digest of `results`."""
        if self.salt is None:
            raise exceptions.SecretNotFound("wolfram-salt not specified in secrets.json.")

        values = [f"{k}{v}" for k, v in results.items()]
        data = f"{self.salt}{''.join(values)}"
        encoded = data.encode(encoding="utf-8")
        signature = hashlib.md5(encoded)
        return signature.hexdigest().upper()

    def parameters(self, query: str, **kwargs: dict) -> dict:
        """Generates a reasonable default dictionary of parameters (plus extras via kwargs)."""
        if self.id is None:
            raise exceptions.SecretNotFound("wolfram-id not specified in secrets.json.")

        params = {
            "appid": self.id,
            "format": "plaintext",
            "input": query,
            "output": "json",
            "reinterpret": "true"
        }

        params.update(kwargs)
        return params

    async def request(self, path: str) -> str:
        """Sends a HTTP GET request to the WolframAlpha API."""
        url = yarl.URL(path, encoded=True)

        async with self.session.get(url) as resp:
            data = await resp.read()
            data = data.decode("utf-8")
            return data

    async def fullresults(self, params: dict) -> dict:
        """Returns results from the Full Results API."""
        encoder = urllib.parse.quote_plus
        bypass = lambda string, safe, encoding, errors: string

        params = {k: encoder(v) for k, v in sorted(params.items())}
        encoded = urllib.parse.urlencode(params, quote_via=bypass)
        path = f"query.jsp?{encoded}"

        if self.hashing:
            digest = self.digest(params)
            path += f"&sig={digest}"

        path = f"{self.v2base}/{path}"
        data = await self.request(path)

        try:
            data = ujson.loads(data)
            data = data["queryresult"]
        except (ValueError, KeyError):
            data = {}

        return data
