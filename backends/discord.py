import exceptions
import model

from discord.ext import commands
import datetime as dt
import typing as t
import discord
import base64
import ujson
import http

class User:
    """Represents a user in Discord."""
    def __init__(self, ctx: commands.Context, token: str, identifier: int) -> None:
        self.identifier = identifier
        self.token = token
        self.ctx = ctx

    async def create_event(self, channel: discord.VoiceChannel, name: str, description: str, *, time: t.Optional[dt.datetime]=None) -> None:
        """Creates a Guild Event for `channel` with a name, description and optional time."""
        time = time or dt.datetime.utcnow() + dt.timedelta(seconds=5)

        payload = {
            "channel_id": channel.id,
            "description": description,
            "entity_metadata": None,
            "entity_type": 2,
            "name": name,
            "privacy_level": 2,
            "scheduled_start_time": time.isoformat()
        }

        properties = {
            "os": "Linux",
            "browser": "Firefox",
            "device": "",
            "system_locale": "en-AU",
            "browser_user_agent": "Mozilla/6.9 Gecko/20100101 Firefox/9001.0.0",
            "browser_version": "9001.0.0",
            "os_version": "5.0.0",
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": 100054,
            "client_event_source": None
        }

        properties = base64.b64encode(ujson.dumps(properties).encode("utf-8")).decode("utf-8")
        headers = {"Authorization": self.token, "X-Super-Properties": properties}
        await Backend.post(f"guilds/{channel.guild.id}/events", json=payload, headers=headers)

class Webhooks:
    @staticmethod
    async def create(channel: discord.TextChannel, name: str) -> None:
        """Creates a new webhook in `channel` with the name of `name`."""
        if Backend.token is None:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        headers = {"Authorization": f"Bot {Backend.token}"}
        payload = {"name": name}
        endpoint = f"channels/{channel.id}/webhooks"
        await Backend.post(endpoint, json=payload, headers=headers)

    @staticmethod
    async def move(webhook: discord.Webhook, channel: discord.TextChannel) -> None:
        """Moves `webhook` from its current channel to `channel`."""
        if Backend.token is None:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        headers = {"Authorization": f"Bot {Backend.token}"}
        payload = {"channel_id": channel.id}
        endpoint = f"webhooks/{webhook.id}"
        await Backend.post(endpoint, json=payload, headers=headers)

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
        """Returns a URL for connecting to a gateway."""
        if not cls.gateway_url:
            result = await cls.get("gateway")
            cls.gateway_url = result["url"]

        return cls.gateway_url

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
