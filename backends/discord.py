import exceptions
import model

import discord
import ujson
import http

class Webhooks:
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        cls.base = "https://discord.com/api/v9"
        cls.session = bot.session
        cls.token: bot.secrets.get("discord-token", None)

    @classmethod
    async def post(cls, endpoint: str, **kwargs: dict) -> dict:
        """Sends a HTTP POST request to the Discord API."""
        async with cls.session.post(f"{cls.base}/{endpoint}", **kwargs) as response:
            if response.status != http.HTTPStatus.OK:
                data = await response.json(encoding="utf-8", loads=ujson.loads)
                error = data.get("message", None)
                raise exceptions.HTTPUnexpected(response.status, error)

        if "read" in kwargs and kwargs["read"] == True:
            return await response.json(encoding="utf-8", loads=ujson.loads)

    @classmethod
    async def create(cls, channel: discord.TextChannel, name: str) -> None:
        """Creates a webhook in `channel` by sending a raw HTTP request."""
        if cls.token is None:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        headers = {"Authorization": f"Bot {cls.token}"}
        payload = {"name": name}
        endpoint = f"channels/{channel.id}/webhooks"
        await cls.post(endpoint, json=payload, headers=headers)

    @classmethod
    async def move(cls, webhook: discord.Webhook, channel: discord.TextChannel) -> None:
        """Moves a webhook to `channel` by sending a raw HTTP request."""
        if cls.token is None:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        headers = {"Authorization": f"Bot {cls.token}"}
        payload = {"channel_id": channel.id}
        endpoint = f"webhooks/{webhook.id}"
        await cls.post(endpoint, json=payload, headers=headers)

def setup(bot: model.Bakerbot) -> None:
    Webhooks.setup(bot)
