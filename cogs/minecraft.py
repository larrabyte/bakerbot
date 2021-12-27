from backends import minecraft
import utilities
import model

from discord.ext import commands
import discord

class Minecraft(commands.Cog):
    """Commands related to Minecraft."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.colour_strings = [
            # Strings used by Minecraft to change the colour of text.
            "§4", "§c", "§6", "§e", "§2", "§a", "§b", "§3", "§1", "§9", "§d",
            "§5", "§f", "§7", "§8", "§0", "§r", "§l", "§o", "§n", "§m", "§k"
        ]

        self.bot = bot

    @commands.group(invoke_without_subcommand=True, aliases=["minecraft"])
    async def mc(self, ctx: commands.Context) -> None:
        """The parent command for all things Minecraft-related."""
        summary = ("You've encountered Bakerbot's Minecraft command group! "
                   "See `$help minecraft` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @mc.command()
    async def ping(self, ctx: commands.Context, address: str) -> None:
        """Send a SLP request to a Minecraft server."""
        if ":" not in address:
            endpoint = address
            port = 25565
        else:
            components = address.split(":", maxsplit=1)
            endpoint = components[0]
            port = int(components[1])

        async with ctx.typing():
            response = await minecraft.Backend.ping(endpoint, port)

            reply = (f"Response received from {address}.\n"
                     f" • **Release name:** {response.version_name}\n"
                     f" • **Protocol version:** {response.version_protocol}\n"
                     f" • **Players online:** {response.players_online}/{response.player_max}\n")

            if response.sample:
                players = ", ".join(p["name"] for p in response.sample)
                players = discord.utils.escape_markdown(players)
                reply += f"   • **Sample given by server:** {players}\n"

            if response.motd:
                for replaceable in self.colour_strings:
                    response.motd = response.motd.replace(replaceable, "")

                response.motd = discord.utils.escape_markdown(response.motd)
                reply += f" • **MOTD:** {response.motd}\n"

            modded = f"Yes, {response.modded_type}" if response.modded_type is not None else "No"
            reply += f" • **Modded?** {modded}\n"

            if response.mods is not None:
                mod_list = ", ".join(m["modid"] for m in response.mods)
                reply += f"   • **Mod list:** {mod_list}\n"

            # Enough players and/or mods will push the list over the character limit.
            reply = utilities.Limits.limit(reply, utilities.Limits.MESSAGE_CHARACTERS)
            await ctx.reply(reply)

def setup(bot: model.Bakerbot) -> None:
    cog = Minecraft(bot)
    bot.add_cog(cog)
