import exceptions
import model

import discord
import aiohttp
import ujson
import http

class Webhooks:
    """Experimental Discord webhook methods (ignores rate-limits)."""
    base = "https://discord.com/api/v9"
    session: aiohttp.ClientSession
    token: str

    @classmethod
    async def create(cls, channel: discord.TextChannel, name: str) -> None:
        """Creates a webhook in `channel` by sending a raw HTTP request."""
        if cls.token is None:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        headers = {"Authorization": f"Bot {cls.token}"}
        payload = {"name": name}

        endpoint = f"{cls.base}/channels/{channel.id}/webhooks"
        async with cls.session.post(endpoint, json=payload, headers=headers) as response:
            if response.status != http.HTTPStatus.OK:
                data = await response.json(encoding="utf-8", loads=ujson.loads)
                error = data.get("message", None)
                raise exceptions.HTTPUnexpected(response.status, error)

    @classmethod
    async def move(cls, webhook: discord.Webhook, channel: discord.TextChannel) -> None:
        """Moves a webhook to `channel` by sending a raw HTTP request."""
        if cls.token is None:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        headers = {"Authorization": f"Bot {cls.token}"}
        payload = {"channel_id": channel.id}

        endpoint = f"{cls.base}/webhooks/{webhook.id}"
        async with cls.session.patch(endpoint, json=payload, headers=headers) as response:
            if response.status != http.HTTPStatus.OK:
                data = await response.json(encoding="utf-8", loads=ujson.loads)
                error = data.get("message", None)
                raise exceptions.HTTPUnexpected(response.status, error)

def setup(bot: model.Bakerbot) -> None:
    Webhooks.session = bot.session
    Webhooks.token = bot.secrets.get("discord-token", None)
