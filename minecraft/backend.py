import minecraft.types as types

import dataclasses
import asyncio
import struct
import json
import time
import enum

class Empty(Exception):
    """Expected a response, got nothing."""
    pass

@dataclasses.dataclass
class Ping:
    """An SLP response from a Minecraft server."""
    version: str
    protocol: int
    maximum_players: int
    online_players: int
    user_sample: list[str]
    message_of_the_day: str
    favicon: str
    modded: bool

class Identifier(enum.Enum):
    """Identifies the type of a packet."""
    GENERIC = b"\x00"
    PING_PONG = b"\x01"

class Packet:
    """The packet crafting routine container."""
    @staticmethod
    def handshake(address: str, port: int) -> bytes:
        """Create a handshake packet."""
        # Corresponds to Minecraft 1.19.
        version = types.Integer(759)
        status = types.Integer(1)

        data = (
            bytes(version) +
            bytes(types.String(address)) +
            struct.pack("!H", port) +
            bytes(status)
        )

        return encapsulate(Identifier.GENERIC, data)

    @staticmethod
    def ping() -> bytes:
        """Create a ping packet."""
        timestamp = time.time_ns() // 1000000
        data = struct.pack("!Q", timestamp)
        return encapsulate(Identifier.PING_PONG, data)

def encapsulate(identifier: Identifier, data: bytes) -> bytes:
    """Encapsulate arbitrary data into a packet."""
    payload = identifier.value + data
    size = types.Integer(len(payload))
    return bytes(size) + payload

async def query(address: str, port: int) -> types.Payload:
    """Get SLP information from a Minecraft server."""
    connection = asyncio.open_connection(address, port)
    rx, tx = await asyncio.wait_for(connection, timeout=5)

    # Send handshake, request and ping packets.
    # The ping packet is optional, but servers seem to
    # respond faster when it's present.
    initial = Packet.handshake(address, port)
    request = encapsulate(Identifier.GENERIC, b"")
    ping = Packet.ping()

    tx.write(initial)
    tx.write(request)
    tx.write(ping)
    await tx.drain()

    response = await rx.read()
    tx.close()
    await tx.wait_closed()

    length, alpha = types.Integer.parse(response)
    identifier, beta = types.Integer.parse(response[alpha:])
    data, gamma = types.Integer.parse(response[alpha + beta:])
    payload = response[alpha + beta + gamma:alpha + beta + gamma + data]

    if not payload:
        raise Empty

    return json.loads(payload)

async def ping(address: str, port: int) -> Ping:
    """Ping a Minecraft server."""
    payload = await query(address, port)
    message = payload["description"]

    # MOTDs require some special handling.
    if not isinstance(message, str):
        initial = message.get("text") or ""
        addon = "".join(extra.get("text") or "" for extra in message.get("extra") or [])
        message = initial + addon

    return Ping(
        version=payload["version"]["name"],
        protocol=payload["version"]["protocol"],
        maximum_players=payload["players"]["max"],
        online_players=payload["players"]["online"],
        user_sample=[player["name"] for player in payload["players"]["sample"] or []],
        message_of_the_day=message,
        favicon=payload["favicon"],
        modded="modinfo" in payload or "forgeData" in payload
    )
