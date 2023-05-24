import typing

class Payload(typing.TypedDict):
    """The base format of any response."""
    result: typing.Literal["ok", "error"]

class Object(typing.TypedDict):
    """The base format of most standalone API objects."""
    id: str
    type: str

class Chapter(typing.TypedDict):
    """The format of a chapter from the manga aggregate endpoint."""
    chapter: str
    id: str
    others: list[str]
    count: int

class Volume(typing.TypedDict):
    """The format of a volume from the manga aggregate endpoint."""
    volume: str
    count: int
    chapters: dict[str, Chapter]

class Routes(typing.TypedDict):
    """The format of the image delivery metadata from the CDN chapter request endpoint."""
    hash: str
    data: list[str]
    dataSaver: list[str]

class TagAttributes(typing.TypedDict):
    """The format of a TagAttributes object."""
    name: dict[str, str]
    description: dict[str, str]
    group: str
    version: int

class AuthorAttributes(typing.TypedDict):
    """The format of an AuthorAttributes object."""
    name: str
    imageUrl: str
    biography: dict[str, str]
    twitter: str | None
    pixiv: str | None
    melonBook: str | None
    fanBox: str | None
    booth: str | None
    nicoVideo: str | None
    skeb: str | None
    fantia: str | None
    tumblr: str | None
    youtube: str | None
    weibo: str | None
    naver: str | None
    website: str | None
    version: int
    createdAt: str
    updatedAt: str

class Relationship(Object, total=False):
    """The format of a Relationship object."""
    related: str
    attributes: dict[str, str] | None

class Tag(Object):
    """The format of a Tag object."""
    attributes: TagAttributes
    relationships: list[Relationship]

class Author(Object):
    """The format of an Author object."""
    attributes: AuthorAttributes
    relationships: list[Relationship]

class MangaAttributes(typing.TypedDict):
    """The format of a MangaAttributes object."""
    title: dict[str, str]
    altTitles: list[dict[str, str]]
    description: dict[str, str]
    isLocked: bool
    links: dict[str, str]
    originalLanguage: str
    lastVolume: str | None
    lastChapter: str | None
    publicationDemographic: str | None
    status: str | None
    year: int | None
    contentRating: str
    chapterNumbersResetOnNewVolume: bool
    availableTranslatedLanguages: list[str]
    latestUploadedChapter: str
    tags: list[Tag]
    state: str
    version: int
    createdAt: str
    updatedAt: str

class Manga(Object):
    """The format of a Manga object."""
    attributes: MangaAttributes
    relationships: list[Relationship]

class Error(Payload):
    """The format of an Error object."""
    id: str
    status: int
    title: str
    detail: str

class ErrorResponse(Payload):
    """The format of an ErrorResponse object."""
    errors: list[Error]

class AuthorResponse(Payload):
    """The format of an AuthorResponse object."""
    response: str
    data: Author

class AggregateResponse(Payload):
    """The format of a response from the manga aggregate endpoint."""
    # NOTE: This doesn't seem to be documented, but an empty aggregate
    # is returned as an empty list rather than as a dictionary with no keys.
    volumes: dict[str, Volume] | list

class CDNResponse(Payload):
    """The format of a response from the CDN chapter request endpoint."""
    baseUrl: str
    chapter: Routes

class MangaList(Payload):
    """The format of a MangaList object."""
    response: typing.Literal["collection"]
    data: list[Manga]
    limit: int
    offset: int
    total: int
