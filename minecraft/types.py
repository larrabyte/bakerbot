import typing

class Integer:
    """A variable-length integer."""
    def __init__(self, value: int):
        self.bytes = bytes()

        while (value & ~0x7F) != 0:
            # If there are set bits higher from bit 7 onwards (zero-indexed),
            # take the last 7 bits and set bit 7 to indicate more bits are needed.
            self.bytes += ((value & 0x7F) | 0x80).to_bytes(1, "little")
            value >>= 7

        self.bytes += value.to_bytes(1, "little")

    def __int__(self) -> int:
        value = 0
    
        for index, byte in enumerate(self.bytes):
            value |= (byte & 0x7F) << (index * 7)
            if (byte & 0x80) != 0x80:
                break

        return value

    def __len__(self) -> int:
        return len(self.bytes)

    def __bytes__(self) -> bytes:
        return self.bytes

    @classmethod
    def parse(cls, data: bytes) -> tuple[int, int]:
        """Parse a stream of bytes into an (integer, length) pair."""
        value, bytecount = (0, 0)

        for index, byte in enumerate(data):
            value |= (byte & 0x7F) << (index * 7)
            if (byte & 0x80) != 0x80:
                bytecount = index + 1
                break

        return (value, bytecount)

class String:
    """A variable-length string."""
    def __init__(self, string: str):
        self.string = string

    def __bytes__(self) -> bytes:
        length = Integer(len(self.string))
        return bytes(length) + bytes(self.string, "utf-8")

class Version(typing.TypedDict):
    """The format of the version entry in an SLP response."""
    name: str
    protocol: int

class Player(typing.TypedDict):
    """The format of a player in an SLP sample list."""
    name: str
    id: str

class Players(typing.TypedDict):
    """The format of the player entry in an SLP response."""
    max: int
    online: int
    sample: list[Player] | None

class Chat(typing.TypedDict):
    """The format of a JSON Chat object."""
    text: typing.NotRequired[str]

    # This is an incomplete listing.
    # Not that it matters, since we don't use these anyway.
    bold: bool
    italic: bool
    underlined: bool
    strikethrough: bool
    obfuscated: bool

    extra: typing.NotRequired[list["Chat"]]

class Payload(typing.TypedDict):
    """The format of an SLP payload for servers running Minecraft 1.7 or above."""
    version: Version
    players: Players
    description: str | Chat
    favicon: str
