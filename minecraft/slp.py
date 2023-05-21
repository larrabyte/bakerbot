import dataclasses
import asyncio
import struct
import time
import json

class VariableInteger:
    """A variable-length integer, used in packets sent by Minecraft servers."""
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
        """Parse a stream of bytes encoding a `VariableInteger` into an (integer, length) pair."""
        value, bytecount = (0, 0)

        for index, byte in enumerate(data):
            value |= (byte & 0x7F) << (index * 7)
            if (byte & 0x80) != 0x80:
                bytecount = index + 1
                break

        return (value, bytecount)

class VariableString:
    """A variable-length string, used in packets sent by Minecraft servers."""
    def __init__(self, string: str):
        self.string = string

    def __bytes__(self) -> bytes:
        length = VariableInteger(len(self.string))
        return bytes(length) + bytes(self.string, "utf-8")

@dataclasses.dataclass
class Response:
    """Information about a Minecraft server."""
    version_name: str
    version_protocol: int
    players_maximum: int
    players_online: int
    sample: list[dict[str, str]] | None
    message_of_the_day: str
    favicon: str

    # Forge-specific?
    modded: str | None
    mods: list[dict[str, str]] | None

    @classmethod
    def parse(cls, payload: bytes) -> "Response":
        """Parse a stream of bytes into an instance of `Response`."""
        data = json.loads(payload)

        motd = (
            data["description"].get("text", "") +  "".join(e["text"] for e in data["description"].get("extra", []))
            if isinstance(data["description"], dict) else
            data["description"]
        )

        assert isinstance(motd, str)

        metadata = data.get("modinfo")
        modded = metadata["type"] if metadata is not None else None
        mods = metadata["modList"] if metadata is not None else None

        return cls(
            version_name=data["version"]["name"],
            version_protocol=data["version"]["protocol"],
            players_maximum=data["players"]["max"],
            players_online=data["players"]["online"],
            sample=data["players"].get("sample"),
            message_of_the_day=motd,
            favicon=data.get("favicon"),
            modded=modded,
            mods=mods
        )

def encapsulate(id: bytes, data: bytes) -> bytes:
    """Encapsulate the given data into a Minecraft packet."""
    payload = id + data
    size = VariableInteger(len(payload))
    return bytes(size) + payload

def handshake(address: str, port: int) -> bytes:
    """Create a Minecraft handshake packet."""
    # Corresponds to Minecraft 1.8.x.
    version = VariableInteger(47)
    status = VariableInteger(1)

    data = (
        bytes(version) +
        bytes(VariableString(address)) +
        struct.pack("!H", port) +
        bytes(status)
    )

    return encapsulate(b"\x00", data)

def ping() -> bytes:
    """Create a Minecraft ping packet."""
    timestamp = time.time_ns() // 1000000
    data = struct.pack("!Q", timestamp)
    return encapsulate(b"\x01", data)

async def query(address: str, port: int) -> Response | None:
    """Ping a Minecraft server."""
    connection = asyncio.open_connection(address, port)
    rx, tx = await asyncio.wait_for(connection, timeout=5)

    # Send an initial handshake packet.
    initial = handshake(address, port)
    tx.write(initial)
    await tx.drain()

    # Send a request packet.
    request = encapsulate(b"\x00", b"")
    tx.write(request)
    await tx.drain()

    # Send a ping packet so the server responds faster.
    # Seems to just wait for a timeout otherwise.
    speed = ping()
    tx.write(speed)
    await tx.drain()

    response = await rx.read()
    tx.close()
    await tx.wait_closed()

    _, a = VariableInteger.parse(response)
    _, b = VariableInteger.parse(response[a:])
    l, c = VariableInteger.parse(response[a + b:])

    payload = response[a + b + c:a + b + c + l]

    if len(payload) > 0:
        return Response.parse(payload)

    return None
