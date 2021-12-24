import exceptions
import model

from discord.ext import commands
import datetime as dt
import discord
import base64
import ujson
import http

class User:
    """Represents a Discord user."""
    def __init__(self, ctx: commands.Context, token: str, identifier: int) -> None:
        self.identifier = identifier
        self.token = token
        self.ctx = ctx

    async def create_event(self, channel: discord.VoiceChannel, name: str, description: str, time: dt.datetime) -> None:
        """Create a Guild Event for `channel` with a name, description and timestamp."""
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

        dumped_properties = ujson.dumps(properties).encode("utf-8")
        serialised_properties = base64.b64encode(dumped_properties).decode("utf-8")

        headers = {
            "Authorization": self.token,
            "X-Super-Properties": serialised_properties
        }

        await Backend.post(f"guilds/{channel.guild.id}/events", json=payload, headers=headers)

class Webhooks:
    @staticmethod
    async def create(channel: discord.TextChannel, name: str) -> None:
        """Create a new webhook in `channel`."""
        if Backend.token is None:
            raise model.SecretNotFound("discord-token not specified in secrets.json.")

        headers = {"Authorization": f"Bot {Backend.token}"}
        payload = {"name": name}
        endpoint = f"channels/{channel.id}/webhooks"
        await Backend.post(endpoint, json=payload, headers=headers)

    @staticmethod
    async def move(webhook: discord.Webhook, channel: discord.TextChannel) -> None:
        """Move `webhook` from its current channel to the specified `channel`."""
        if Backend.token is None:
            raise model.SecretNotFound("discord-token not specified in secrets.json.")

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

    @classmethod
    async def get(cls, endpoint: str, **kwargs: dict) -> dict:
        """Send a HTTP GET request to the Discord REST API."""
        async with Backend.session.get(f"{Backend.base}/{endpoint}", **kwargs) as response:
            data = await response.json(encoding="utf-8", loads=ujson.loads)

            if response.status != http.HTTPStatus.OK:
                error = data.get("message", None)
                raise exceptions.HTTPUnexpected(response.status, error)

            return data

    @classmethod
    async def post(cls, endpoint: str, **kwargs: dict) -> dict:
        """Send a HTTP POST request to the Discord REST API."""
        async with Backend.session.post(f"{Backend.base}/{endpoint}", **kwargs) as response:
            data = await response.json(encoding="utf-8", loads=ujson.loads)

            if response.status != http.HTTPStatus.OK:
                error = data.get("message", None)
                raise exceptions.HTTPUnexpected(response.status, error)

            return data

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
