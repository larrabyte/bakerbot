import exceptions
import model

import urllib.parse
import multidict
import hashlib
import ujson
import http
import yarl

class Source:
    """Represents WolframAlpha's `Source` API object."""
    def __init__(self, data: dict) -> None:
        self.url: str = data["url"]
        self.text: str = data["text"]

class Image:
    """Represents WolframAlpha's `Image` API object."""
    def __init__(self, data: dict) -> None:
        self.source: str = data["src"]
        self.alternate: str = data["alt"]
        self.title: str = data["alt"]
        self.width: int = data["width"]
        self.height: int = data["height"]
        self.type: str = data["type"]
        self.themes: str = data["themes"]
        self.colour_invertable: bool = data["colorinvertable"]

class Subpod:
    """Represents WolframAlpha's `Subpod` API object."""
    def __init__(self, data: dict) -> None:
        self.title: str = data["title"]

        self.image: Image | None = None
        if "img" in data:
            image = data["img"]
            wrapper = Image(image)
            self.image = wrapper

        self.plaintext: str | None = data.get("plaintext", None)

class Pod:
    """Represents WolframAlpha's `Pod` API object."""
    def __init__(self, data: dict) -> None:
        self.title: str = data["title"]
        self.scanner: str = data["scanner"]
        self.id: str = data["id"]
        self.posititon: str = data["position"]
        self.error: bool = data["error"]

        self.subpods: list[Subpod] = []
        for subpod in data.get("subpods", []):
            wrapper = Subpod(subpod)
            self.subpods.append(wrapper)

        self.states: list[dict[str, str]] = []
        for state in data.get("states", []):
            if "states" in state:
                for substate in state["states"]:
                    self.states.append(substate)
            else:
                self.states.append(state)

class Result:
    """Represents WolframAlpha's `QueryResult` API object."""
    def __init__(self, data: dict) -> None:
        data = data["queryresult"]
        self.success: bool = data["success"]
        self.datatypes: str = data["datatypes"]
        self.timed_out: str = data["timedout"]
        self.timed_out_pods: str = data["timedoutpods"]
        self.timing: float = data["timing"]
        self.parse_timing: float | None = data.get("parsetiming", None)
        self.parse_timed_out: bool = data["parsetimedout"]
        self.recalculate: str = data["recalculate"]
        self.id: str = data["id"]
        self.host: str = data["host"]
        self.server: str = data["server"]
        self.related: str = data["related"]
        self.version: str = data["version"]
        self.input: str | None = data.get("inputstring", None)

        self.pods: list[Pod] = []
        for pod in data.get("pods", []):
            wrapper = Pod(pod)
            self.pods.append(wrapper)

        self.error_message: str | None = None

        if data["error"]:
            # The API will return a dictionary in this field if it's not false.
            self.error_message = data["error"]["msg"]

class Query:
    """Represents the results of a WolframAlpha API request."""
    def __init__(self, **kwargs: dict) -> None:
        if Backend.id is None:
            raise model.SecretNotFound("wolfram-id not specified in secrets.json.")

        self.parameters = multidict.MultiDict(appid=Backend.id, output="json", **kwargs)

    def digest(self) -> str:
        """Return the MD5 digest for this query."""
        if Backend.salt is None:
            raise model.SecretNotFound("wolfram-salt not specified in secrets.json.")

        items = sorted(self.parameters.items())
        encoded = multidict.MultiDict((k, urllib.parse.quote_plus(v)) for k, v in items)
        values = ''.join(f"{k}{v}" for k, v in encoded.items())
        data = f"{Backend.salt}{values}"

        signature = hashlib.md5(data.encode(encoding="utf-8"))
        return signature.hexdigest().upper()

class Backend:
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        cls.base = "https://api.wolframalpha.com/"
        cls.session = bot.session
        cls.id = bot.secrets.get("wolfram-id", None)
        cls.salt = bot.secrets.get("wolfram-salt", None)
        cls.hashing = bot.secrets.get("wolfram-hash", False)

    @classmethod
    async def get(cls, endpoint: str, **kwargs: dict) -> dict:
        """Send a HTTP GET request to the WolframAlpha API."""
        # aiohttp doesn't know how to canonicalise correctly...
        parameters = kwargs.pop("params")
        query = urllib.parse.urlencode(parameters, quote_via=urllib.parse.quote_plus)
        absolute = f"{cls.base}/{endpoint}?{query}"
        url = yarl.URL(absolute, encoded=True)

        async with cls.session.get(url, **kwargs) as response:
            data = await response.read()

            if response.status != http.HTTPStatus.OK:
                try: formatted = ujson.loads(data)
                except ValueError: formatted = {}
                error = str(formatted.get("errors", None))
                raise exceptions.HTTPUnexpected(response.status, error)

            return ujson.loads(data)

    @classmethod
    async def request(cls, query: Query) -> Result:
        """Return a `Result` object from WolframAlpha's Full Results API."""
        parameters = multidict.MultiDict(query.parameters, sig=query.digest())
        data = await cls.get(f"v2/query.jsp", params=parameters)
        return Result(data)

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
