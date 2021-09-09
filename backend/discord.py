import exceptions
import model

import discord
import ujson

class Webhooks:
    """Experimental Discord webhook methods (ignores rate-limits)."""
    base = "https://discord.com/api/v9"

    @classmethod
    async def create(cls, bot: model.Bakerbot, channel: discord.TextChannel, name: str) -> None:
        """Creates a webhook in `channel` by sending a raw HTTP request."""
        token = bot.secrets["discord-token"]
        headers = {"Authorization": f"Bot {token}"}
        payload = {"name": name}

        path = f"{cls.base}/channels/{channel.id}/webhooks"
        response = await bot.session.post(path, json=payload, headers=headers)

        if response.status != 200:
            data = await response.json(encoding="utf-8", loads=ujson.loads)

            if "message" in data:
                message = data["message"]
                raise exceptions.HTTPUnexpectedResponse(message)

            raise exceptions.HTTPBadStatus(200, response.status)

    @classmethod
    async def move(cls, bot: model.Bakerbot, webhook: discord.Webhook, channel: discord.TextChannel) -> None:
        """Moves a webhook to `channel` by sending a raw HTTP request."""
        token = bot.secrets["discord-token"]
        headers = {"Authorization": f"Bot {token}"}
        payload = {"channel_id": channel.id}

        path = f"{cls.base}/webhooks/{webhook.id}"
        response = await bot.session.patch(path, json=payload, headers=headers)

        if response.status != 200:
            data = await response.json(encoding="utf-8", loads=ujson.loads)

            if "message" in data:
                message = data["message"]
                raise exceptions.HTTPUnexpectedResponse(message)

            raise exceptions.HTTPBadStatus(200, response.status)
