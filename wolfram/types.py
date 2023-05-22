import dataclasses
import multidict
import typing

class Error(typing.TypedDict):
    """The format of an Error object."""
    code: str
    msg: str

class State(typing.TypedDict):
    """The format of a State object."""
    name: str
    input: str

class States(typing.TypedDict):
    """The format of a States object."""
    count: int
    value: str
    delimiters: str
    states: list[State]

class Image(typing.TypedDict, total=False):
    """The format of an Image object."""
    src: typing.Required[str]
    alt: typing.Required[str]
    title: typing.Required[str]
    width: typing.Required[int]
    height: typing.Required[int]

class Subpod(typing.TypedDict, total=False):
    """The format of a Subpod object."""
    title: typing.Required[str]

    img: Image

class Pod(typing.TypedDict, total=False):
    """The format of a Pod object."""
    title: typing.Required[str]
    error: typing.Required[typing.Literal[False] | Error]
    position: typing.Required[str]
    scanner: typing.Required[str]
    id: typing.Required[str]
    numsubpods: typing.Required[int]

    subpods: list[Subpod]
    states: list[State | States]

class Query(typing.TypedDict, total=False):
    """The format of a Query Result object."""
    success: typing.Required[bool]
    error: typing.Required[typing.Literal[False] | Error]
    numpods: typing.Required[int]
    version: typing.Required[str]
    datatypes: typing.Required[str]
    timing: typing.Required[float]
    timedout: typing.Required[str]
    parsetiming: typing.Required[float]
    parsetimedout: typing.Required[bool]
    recalculate: typing.Required[str]

    pods: list[Pod]

class Payload(typing.TypedDict):
    """The format of an API response."""
    queryresult: Query

@dataclasses.dataclass
class Cherry:
    """The equivalent of a State object."""
    name: str
    input: str

@dataclasses.dataclass
class Capsule:
    """The equivalent of a Pod object."""
    id: str
    title: str
    pictures: list[str]
    cherries: list[Cherry]

@dataclasses.dataclass
class Response:
    """Answers from Wolfram|Alpha."""
    parameters: multidict.MultiDict
    capsules: list[Capsule]
