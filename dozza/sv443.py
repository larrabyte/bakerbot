import dataclasses
import aiohttp
import typing
import json
import enum

class Language(enum.Enum):
    """The possible languages that a joke can be written in."""
    CZECH = "cs"
    GERMAN = "de"
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    PORTUGESE = "pt"

class Category(enum.Enum):
    """The categories of jokes that can be requested."""
    PROGRAMMING = "Programming"
    MISCELLANEOUS = "Misc"
    DARK = "Dark"
    PUN = "Pun"
    SPOOKY = "Spooky"
    CHRISTMAS = "Christmas"

class Blacklist(enum.Enum):
    """The types of jokes that can be excluded from a request."""
    NSFW = "nsfw"
    RELIGIOUS = "religious"
    POLITICAL = "political"
    RACIST = "racist"
    SEXIST = "sexist"
    EXPLICIT = "explicit"

class Type(enum.Enum):
    """The type of jokes available."""
    SINGLE = "single"
    TWOPART = "twopart"

class Flags(typing.TypedDict):
    """A dictionary indicating what types of jokes have been blacklisted."""
    nsfw: bool
    religious: bool
    political: bool
    racist: bool
    sexist: bool
    explicit: bool

class Payload(typing.TypedDict):
    """The base format of any response from the API."""
    error: bool

class Response(Payload):
    """The format for a successful response from the API."""
    category: Category
    type: Type
    flags: Flags
    id: int
    safe: bool
    lang: Language

class ResponseSingle(Response):
    """The format of a single-type joke response from the API."""
    joke: str

class ResponseTwoPart(Response):
    """The format of a two-part-type joke response from the API."""
    setup: str
    delivery: str

class Error(Payload):
    """The format of a failed response from the API."""
    internalError: bool
    code: int
    message: str
    causedBy: list[str]
    additionalInfo: str
    timestamp: int

@dataclasses.dataclass
class Joke:
    """Holds funny stuff."""
    quip: str
    followup: str | None

async def request(session: aiohttp.ClientSession) -> ResponseSingle | ResponseTwoPart:
    """Request a joke from the sv443 JokeAPI."""
    async with session.get("https://v2.jokeapi.dev/joke/Any") as response:
        data = await response.read()
        bundle = json.loads(data)

        if bundle["error"]:
            raise RuntimeError(bundle["message"])

        return bundle

async def funny(session: aiohttp.ClientSession) -> Joke:
    """Get a fucking joke."""
    bundle = await request(session)

    # One of these fields must exist.
    quip = bundle.get("joke") or bundle.get("setup")
    assert isinstance(quip, str)

    followup = bundle.get("delivery")
    assert isinstance(followup, str | None)

    return Joke(quip, followup)
