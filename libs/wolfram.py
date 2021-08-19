import hashlib
import aiohttp
import urllib
import ujson
import yarl

class Backend:
    """Backend WolframAlpha API wrapper."""
    def __init__(self, secrets: dict, session: aiohttp.ClientSession) -> None:
        self.id = secrets.get("wolfram-id", None)
        self.salt = secrets.get("wolfram-salt", None)
        self.hashing = secrets.get("wolfram-hash", False)
        self.session = session

    def valid(self, results: dict) -> bool:
        """Checks whether WolframAlpha gave a successful response."""
        success = results.get("success", False)
        error = results.get("error", True)
        return success and not error

    @property
    def available(self) -> bool:
        """Checks whether the backend is available for use."""
        token = self.id is not None
        hashoff = self.hashing is False
        hashon = self.hashing is True and self.salt is not None
        return token and (hashon or hashoff)

    def digest(self, results: dict) -> str:
        """Returns an MD5 digest of `results`."""
        if self.salt is None:
            raise RuntimeError("Digest attempted without a salt.")

        values = [f"{k}{v}" for k, v in results.items()]
        data = f"{self.salt}{''.join(values)}"
        encoded = data.encode(encoding="utf-8")
        signature = hashlib.md5(encoded)
        return signature.hexdigest().upper()

    def parameters(self, query: str, **kwargs: dict) -> dict:
        """Generates a reasonable default dictionary of parameters (plus extras via kwargs)."""
        if self.id is None:
            raise RuntimeError("Parameter construction attempted without an ID.")

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

        v2base = "https://api.wolframalpha.com/v2"
        data = await self.request(f"{v2base}/{path}")

        try:
            data = ujson.loads(data)
            data = data["queryresult"]
        except (ValueError, KeyError):
            data = {}

        return data
