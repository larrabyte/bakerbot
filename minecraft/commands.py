from minecraft import slp

import discord.app_commands as application
import discord.ext.commands as commands

import discord
import logging
import limits

class Minecraft(commands.GroupCog):
    def __init__(self, bot: commands.Bot, logger: logging.Logger):
        super().__init__()
        self.logger = logger
        self.bot = bot

        self.colour_patterns = [
            "§4", "§c", "§6", "§e", "§2", "§a", "§b", "§3", "§1", "§9", "§d",
            "§5", "§f", "§7", "§8", "§0", "§r", "§l", "§o", "§n", "§m", "§k"
        ]

    @application.command(description="Ping a Minecraft server.")
    @application.describe(address="The address of the server.")
    async def ping(self, interaction: discord.Interaction, address: str):
        slices = address.split(":", 1)
        endpoint = slices[0]

        # Pings could take a while to come back.
        await interaction.response.defer(thinking=True)

        try:
            port = int(slices[1]) if len(slices) == 2 else 25565
            response = await slp.query(endpoint, port)
        except ValueError:
            return await interaction.followup.send("The specified port is not an integer.")
        except (TimeoutError, OSError):
            return await interaction.followup.send("Connection could not be established.")

        if response is None:
            return await interaction.followup.send("The server did not return a response.")

        reply = (
            f"• **Version:** {discord.utils.escape_markdown(response.version_name)}\n"
            f"• **Protocol version:** {response.version_protocol}\n"
            f"• **Players online:** {response.players_online}/{response.players_maximum}\n"
        )

        if response.sample:
            players = ", ".join(p["name"] for p in response.sample)
            players = discord.utils.escape_markdown(players)
            reply += f"    • **Player sample:** {players}\n"

        if response.message_of_the_day:
            message = response.message_of_the_day
            for replaceable in self.colour_patterns:
                message = message.replace(replaceable, "")

            message = discord.utils.escape_markdown(message.strip())
            reply += f"• **Message of the day:** {message}\n"

        modded = f"Yes, {response.modded}" if response.modded else "No"
        reply += f"• **Modded:** {modded}\n"

        if response.mods:
            mods = ", ".join(m["modid"] for m in response.mods)
            reply += f"    • **Mods:** {mods}\n"

        # Enough players and/or mods will push the list over the character limit.
        reply = limits.limit(reply, limits.MESSAGE_CHARACTERS)
        await interaction.followup.send(reply)
