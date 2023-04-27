from minecraft import slp

import discord.app_commands as application
import discord.ext.commands as commands

import discord
import logging
import limits

COLOUR_PATTERNS = [
    "§4", "§c", "§6", "§e", "§2", "§a", "§b", "§3", "§1", "§9", "§d",
    "§5", "§f", "§7", "§8", "§0", "§r", "§l", "§o", "§n", "§m", "§k"
]

class Minecraft(commands.GroupCog):
    def __init__(self, bot: commands.Bot, logger: logging.Logger) -> None:
        super().__init__()
        self.logger = logger
        self.bot = bot

    @application.command(description="Ping a Minecraft server.")
    @application.describe(address="The address of the server.")
    async def ping(self, interaction: discord.Interaction, address: str) -> None:
        self.logger.info(f"Ping requested for {address}.")
        slices = address.split(":", 1)
        endpoint = slices[0]
        port = int(slices[1]) if len(slices) == 2 else 25565

        # Pings could take a while to come back.
        await interaction.response.defer(thinking=True)
        response = await slp.query(endpoint, port)
    
        if response is None:
            await interaction.followup.send(
                "A connection was successfully made, but the server did not return a response."
            )

            return

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
            for replaceable in COLOUR_PATTERNS:
                message = message.replace(replaceable, "")

            message = discord.utils.escape_markdown(message.strip())
            reply += f"• **Message of the day:** {message}\n"

        modded = f"Yes, {response.modded}" if response.modded is not None else "No"
        reply += f"• **Modded:** {modded}\n"

        if response.mods:
            mods = ", ".join(m["modid"] for m in response.mods)
            reply += f"    • **Mods:** {mods}\n"

        # Enough players and/or mods will push the list over the character limit.
        reply = limits.limit(reply, limits.MESSAGE_CHARACTERS)
        await interaction.followup.send(reply)
