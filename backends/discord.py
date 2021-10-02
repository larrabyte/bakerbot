import exceptions
import model

import typing as t
import discord
import aiohttp
import ujson
import types
import http

class Backend:
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        cls.base = "https://discord.com/api/v9"
        cls.session = bot.session
        cls.token = bot.secrets.get("discord-token", None)
        cls.gateway_url = ""

    @classmethod
    async def get(cls, endpoint: str, **kwargs: dict) -> dict:
        """Sends a HTTP GET request to the Discord API."""
        async with Backend.session.get(f"{Backend.base}/{endpoint}", **kwargs) as response:
            data = await response.json(encoding="utf-8", loads=ujson.loads)

            if response.status != http.HTTPStatus.OK:
                error = data.get("message", None)
                raise exceptions.HTTPUnexpected(response.status, error)

            return data

    @classmethod
    async def post(cls, endpoint: str, **kwargs: dict) -> dict:
        """Sends a HTTP POST request to the Discord API."""
        async with Backend.session.post(f"{Backend.base}/{endpoint}", **kwargs) as response:
            data = await response.json(encoding="utf-8", loads=ujson.loads)

            if response.status != http.HTTPStatus.OK:
                error = data.get("message", None)
                raise exceptions.HTTPUnexpected(response.status, error)

            return data

    @classmethod
    async def gateway(cls) -> str:
        """Returns the result of the `/gateway` endpoint."""
        if not cls.gateway_url:
            result = await cls.get("gateway")
            cls.gateway_url = result["url"]

        return cls.gateway_url

class Webhooks:
    @staticmethod
    async def create(channel: discord.TextChannel, name: str) -> None:
        """Creates a webhook in `channel` by sending a raw HTTP request."""
        if Backend.token is None:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        headers = {"Authorization": f"Bot {Backend.token}"}
        payload = {"name": name}
        endpoint = f"channels/{channel.id}/webhooks"
        await Backend.post(endpoint, json=payload, headers=headers)

    @staticmethod
    async def move(webhook: discord.Webhook, channel: discord.TextChannel) -> None:
        """Moves a webhook to `channel` by sending a raw HTTP request."""
        if Backend.token is None:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        headers = {"Authorization": f"Bot {Backend.token}"}
        payload = {"channel_id": channel.id}
        endpoint = f"webhooks/{webhook.id}"
        await Backend.post(endpoint, json=payload, headers=headers)

class Gateway:
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_QUILD_MEMBERS = 8
    INVALID_SESION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11
    GUILD_SYNC = 12
    START_STREAM = 18
    DELETE_STREAM = 19

    @staticmethod
    async def wait_for(user: "User", predicate: t.Optional[t.Callable]=None) -> dict:
        """Waits for the first event that satisfies the given predicate."""
        while (response := await user.receive()):
            if predicate is None or predicate(response) == True:
                return response

class User:
    def __init__(self, token: str) -> None:
        self.token = token

    async def __aenter__(self) -> "User":
        gateway = await Backend.gateway() + "/?v=9&encoding=json"
        self.ws = await Backend.session.ws_connect(gateway)

        hello = await self.receive()
        self.heartbeat_interval = hello["d"]["heartbeat_interval"]

        authentication = {
            "op": Gateway.IDENTIFY,
            "d": {
                "token": self.token,
                "compress": False,
                "properties": {
                    "os": "Linux",
                    "browser": "Firefox",
                    "device": ""
                }
            }
        }

        await self.send(authentication)

        ready = await self.receive()
        self.session_id = ready["d"]["session_id"]

        return self

    async def __aexit__(self, exception_type: BaseException, exception: Exception, traceback: types.TracebackType) -> None:
        await self.ws.close()

    async def send(self, data: dict) -> None:
        """A wrapper around `send_json()` using ujson."""
        return await self.ws.send_json(data, dumps=ujson.dumps)

    async def receive(self) -> dict:
        """A wrapper around `receive_json()` using ujson."""
        return await self.ws.receive_json(loads=ujson.loads)

    async def connect(self, channel: discord.VoiceChannel) -> None:
        """Connects this user to a voice channel."""
        payload = {
            "op": Gateway.VOICE_STATE_UPDATE,
            "d": {
                "guild_id": channel.guild.id,
                "channel_id": channel.id,
                "self_mute": False,
                "self_deaf": False,
                "self_video": False
            }
        }

        await self.send(payload)

        audio_context = await Gateway.wait_for(self, lambda e: e["op"] == 0 and e["t"] == "VOICE_STATE_UPDATE")
        audio_server = await Gateway.wait_for(self, lambda e: e["op"] == 0 and e["t"] == "VOICE_SERVER_UPDATE")

    async def disconnect(self) -> None:
        """Disconnects the user from any currently connected channels."""
        payload = {
            "op": Gateway.VOICE_STATE_UPDATE,
            "d": {
                "guild_id": None,
                "channel_id": None,
                "self_mute": False,
                "self_deaf": False,
                "self_video": False
            }
        }

        await self.send(payload)

    async def stream(self, channel: discord.VoiceChannel) -> None:
        """Starts a Go Live stream in the user's current voice channel."""
        payload = {
            "op": Gateway.START_STREAM,
            "d": {
                "type": "guild",
                "guild_id": channel.guild.id,
                "channel_id": channel.id,
                "preferred_region": None
            }
        }

        await self.send(payload)

        stream_authorisation = await Gateway.wait_for(self, lambda e: e["op"] == 0 and e["t"] == "STREAM_CREATE")
        stream_context = await Gateway.wait_for(self, lambda e: e["op"] == 0 and e["t"] == "VOICE_STATE_UPDATE")
        stream_server = await Gateway.wait_for(self, lambda e: e["op"] == 0 and e["t"] == "STREAM_SERVER_UPDATE")

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
