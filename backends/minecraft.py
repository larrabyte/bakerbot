import model

import dataclasses
import asyncio
import struct
import typing
import ujson
import time

@dataclasses.dataclass
class Response:
    """The format of a Minecraft server response packet."""
    version_name: str
    version_protocol: int
    player_max: int
    players_online: int
    sample: list[dict[str, str]] | None
    motd: str
    favicon: str

    # Forge-specific?
    modded_type: str | None
    mods: list[dict[str, str]] | None

    @classmethod
    def transform(cls, data: dict) -> "Response":
        """Transform a raw response into an instance of `Response`."""
        description = data["description"]
        if isinstance(description, dict):
            motd = description.get("text", "")
            motd += "".join(e["text"] for e in description.get("extra", []))
        else:
            motd = description

        player_metadata = data["players"]
        sample = player_metadata.get("sample", None)

        favicon = data.get("favicon", None)

        mod_metadata = data.get("modinfo", None)
        modded = mod_metadata["type"] if mod_metadata is not None else None
        mods = mod_metadata["modList"] if mod_metadata is not None else None

        return cls(
            version_name=data["version"]["name"],
            version_protocol=data["version"]["protocol"],
            player_max=data["players"]["max"],
            players_online=data["players"]["online"],
            sample=sample,
            motd=motd,
            favicon=favicon,
            modded_type=modded,
            mods=mods
        )

class Packet:
    @classmethod
    def string(cls, characters: str) -> bytes:
        """Convert a string into a series of bytes, prefixed with a `VarInt` denoting its length."""
        length = VarInt.encode(len(characters))
        return length + characters.encode("utf-8")

    @classmethod
    def encapsulate(cls, packet_id: bytes, data: bytes) -> bytes:
        """Encapsulate `data` into a Minecraft packet."""
        combined = packet_id + data
        length = VarInt.encode(len(combined))
        return length + combined

    @classmethod
    def handshake(cls, address: str, port: int) -> bytes:
        """Create a Minecraft handshake packet."""
        protocol_version = VarInt.encode(757)
        server_address = cls.string(address)
        server_port = struct.pack("!H", port)
        next_state = VarInt.encode(1)
        data = protocol_version + server_address + server_port + next_state
        return Packet.encapsulate(b"\x00", data)

    @classmethod
    def request(cls) -> bytes:
        """Create a Minecraft request packet."""
        return Packet.encapsulate(b"\x00", b"")

    @classmethod
    def ping(cls) -> bytes:
        """Create a Minecraft ping packet. Contains current UNIX timestamp."""
        unix_time = time.time_ns() // 1000000
        converted = struct.pack("!Q", unix_time)
        return Packet.encapsulate(b"\x01", converted)

class VarInt:
    @classmethod
    def encode(cls, value: int) -> bytes:
        """Create an variable-length encoded integer from a Python integer."""
        transformed = bytes()

        while (value & ~0x7F) != 0:
            # If there are set bits higher from bit 7 onwards (zero-indexed),
            # take the last 7 bits and set bit 7 to indicate more bits are needed.
            transformed += ((value & 0x7F) | 0x80).to_bytes(1, "little")
            value >>= 7

        # Afterwards, whatever is left in the lower 7 bits is written as-is.
        transformed += value.to_bytes(1, "little")
        return transformed

    @classmethod
    def decode(cls, bytestream: bytes, *, count: bool=False) -> typing.Union[tuple[int, int], int]:
        """Create a Python integer from a variable-length encoded integer."""
        value = 0
        bytecount = 0

        for index, byte in enumerate(bytestream):
            value |= (byte & 0x7F) << (index * 7)
            if (byte & 0x80) != 0x80:
                bytecount = index + 1
                break

        return (value, bytecount) if count else value

class Backend:
    @classmethod
    async def ping(cls, address: str, port: int) -> Response:
        """Use Minecraft's Server List Ping feature to ping `address`."""
        reader, writer = await asyncio.open_connection(address, port)

        # Send a Handshake packet.
        handshake = Packet.handshake(address, port)
        writer.write(handshake)
        await writer.drain()

        # Send a Request packet.
        request = Packet.encapsulate(b"\x00", b"")
        writer.write(request)
        await writer.drain()

        # Send a Ping packet so the server returns its response faster.
        # The server seems to just wait for a timeout otherwise.
        ping = Packet.ping()
        writer.write(ping)
        await writer.drain()

        # Await the server's response and then close the connection.
        response = await reader.read()
        writer.close()
        await writer.wait_closed()

        response_len, offset_one = VarInt.decode(response, count=True)
        response_id, offset_two = VarInt.decode(response[offset_one:], count=True)
        json_len, offset_three = VarInt.decode(response[offset_one + offset_two:], count=True)

        total_offset = offset_one + offset_two + offset_three
        json_data = response[total_offset:total_offset + json_len]
        json_data = ujson.loads(json_data)
        return Response.transform(json_data)

def setup(bot: model.Bakerbot) -> None:
    pass
