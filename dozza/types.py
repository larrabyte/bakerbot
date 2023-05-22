import dataclasses
import typing
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
    """The base format of any response."""
    error: bool

class Reply(Payload):
    """The format for a successful response."""
    category: Category
    type: Type
    flags: Flags
    id: int
    safe: bool
    lang: Language

class Single(Reply):
    """The format of a single-type joke response."""
    joke: str

class Compound(Reply):
    """The format of a two-part-type joke response."""
    setup: str
    delivery: str

class Error(Payload):
    """The format of a failed response."""
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
