import exceptions
import model

import discord
import ujson
import http

class Backend:
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        cls.base = "https://discord.com/api/v9"
        cls.session = bot.session
        cls.token: bot.secrets.get("discord-token", None)

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

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
