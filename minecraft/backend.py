from minecraft import types

import asyncio
import struct
import json
import time

class Empty(Exception):
    """Expected a response, got nothing."""
    pass

def encapsulate(identifier: types.Identifier, data: bytes) -> bytes:
    """Encapsulate the given data into a Minecraft packet."""
    payload = identifier.value + data
    size = types.Integer(len(payload))
    return bytes(size) + payload

def handshake(address: str, port: int) -> bytes:
    """Create a Minecraft handshake packet."""
    # Corresponds to Minecraft 1.19.
    version = types.Integer(759)
    status = types.Integer(1)

    data = (
        bytes(version) +
        bytes(types.String(address)) +
        struct.pack("!H", port) +
        bytes(status)
    )

    return encapsulate(types.Identifier.GENERIC, data)

def empty() -> bytes:
    """Create a Minecraft ping packet."""
    timestamp = time.time_ns() // 1000000
    data = struct.pack("!Q", timestamp)
    return encapsulate(types.Identifier.PING_PONG, data)

async def query(address: str, port: int) -> types.Payload:
    """Send an SLP request to a server."""
    connection = asyncio.open_connection(address, port)
    rx, tx = await asyncio.wait_for(connection, timeout=5)

    # Send handshake, request and ping packets.
    # The ping packet is optional, but servers seem to
    # respond faster when it's present.
    initial = handshake(address, port)
    request = encapsulate(types.Identifier.GENERIC, b"")
    speed = empty()

    tx.write(initial)
    tx.write(request)
    tx.write(speed)
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

async def ping(address: str, port: int) -> types.Ping:
    """Ping a Minecraft server."""
    payload = await query(address, port)
    motd = payload["description"]

    # MOTDs require some special handling.
    if isinstance(motd, dict):
        initial = motd.get("text") or ""
        addon = "".join(x.get("text") or "" for x in motd.get("extra") or [])
        motd = initial + addon

    return types.Ping(
        version=payload["version"]["name"],
        protocol=payload["version"]["protocol"],
        maximum_players=payload["players"]["max"],
        online_players=payload["players"]["online"],
        user_sample=[player["name"] for player in payload["players"]["sample"] or []],
        message_of_the_day=motd,
        favicon=payload["favicon"],
        modded="modinfo" in payload or "forgeData" in payload
    )
