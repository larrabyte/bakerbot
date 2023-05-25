import discord.app_commands as application
import discord.ext.commands as commands
import minecraft.backend as backend

import discord
import limits
import bot
import re

class Minecraft(commands.GroupCog):
    def __init__(self, bot: bot.Bot):
        super().__init__()
        self.bot = bot

    @application.command(description="Ping a Minecraft (1.7+) server.")
    @application.describe(address="The address of the server.")
    async def ping(self, interaction: discord.Interaction, address: str):
        # Pings could take a while to come back.
        await interaction.response.defer(thinking=True)

        try:
            endpoint, colon, port = address.partition(":")
            port = int(port) if port else 25565
            response = await backend.ping(endpoint, port)
        except ValueError:
            return await interaction.followup.send("The specified port is not an integer.")
        except (TimeoutError, OSError):
            return await interaction.followup.send("A connection could not be established.")
        except backend.Empty:
            return await interaction.followup.send("The server did not return a response.")

        # Enough players/a long enough MOTD will push the reply over the character limit.
        version = discord.utils.escape_markdown(response.version)
        sample = ", ".join(p for p in response.user_sample) or "Unknown"
        modded = "Yes" if response.modded else "No"
        message = response.message_of_the_day.strip()
        message = re.sub("§.", "", message)
        message = discord.utils.escape_markdown(message)

        reply = limits.limit(
            f"- **Version:** {version}.\n"
            f"- **Players online:** {response.online_players}/{response.maximum_players}\n"
            f"- **Player sample:** {sample}\n"
            f"- **Modded:** {modded}\n"
            f"- **Message of the day:** {message}",
            limits.MESSAGE_CHARACTERS
        )

        await interaction.followup.send(reply)
