from minecraft import backend

import discord.app_commands as application
import discord.ext.commands as commands

import discord
import logging
import limits
import re

class Minecraft(commands.GroupCog):
    def __init__(self, bot: commands.Bot, logger: logging.Logger):
        super().__init__()
        self.logger = logger
        self.bot = bot

    @application.command(description="Ping a Minecraft (1.7+) server.")
    @application.describe(address="The address of the server.")
    async def ping(self, interaction: discord.Interaction, address: str):
        slices = address.split(":", 1)
        endpoint = slices[0]

        # Pings could take a while to come back.
        await interaction.response.defer(thinking=True)

        try:
            port = int(slices[1]) if len(slices) == 2 else 25565
            response = await backend.ping(endpoint, port)
            assert response is not None
        except ValueError:
            return await interaction.followup.send("The specified port is not an integer.")
        except (TimeoutError, OSError):
            return await interaction.followup.send("A connection could not be established.")
        except AssertionError:
            return await interaction.followup.send("The server did not return a response.")

        reply = (
            f"• **Version:** {discord.utils.escape_markdown(response.version)}.\n"
            f"• **Players online:** {response.online_players}/{response.maximum_players}.\n"
            f"• **Player sample:** {', '.join(p for p in response.user_sample) or 'Not provided'}.\n"
            f"• **Modded:** {'Yes.' if response.modded else 'Probably not.'}\n"
            f"• **Message of the day:** {discord.utils.escape_markdown(re.sub('§.', '', response.message_of_the_day.strip()))}"
        )

        # Enough players/a long enough MOTD will push the reply over the character limit.
        reply = limits.limit(reply, limits.MESSAGE_CHARACTERS)
        await interaction.followup.send(reply)
