import backends.discord as expcord
import exceptions
import utilities
import model

from discord.ext import commands
import discord
import asyncio
import random
import string
import ujson
import io

class Random(commands.Cog):
    """Random ideas that I come up with every now and again."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    @commands.group(aliases=["discord"])
    async def discordo(self, ctx: commands.Context) -> None:
        """The parent command for Discord experiments."""
        summary = ("You've encountered Bakerbot's Discord experimentation lab! "
                   "See `$help random` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @discordo.command()
    async def typing(self, ctx: commands.Context) -> None:
        """Starts typing in every available text channel."""
        coroutines = [channel.trigger_typing() for channel in ctx.guild.text_channels]
        await asyncio.gather(*coroutines)

    @discordo.command()
    async def live(self, ctx: commands.Context, *, channel: discord.VoiceChannel) -> None:
        """Anybody want an Opcode 18 payload?"""
        if not ("discord-user-token" in self.bot.secrets and "discord-user-id" in self.bot.secrets):
            raise exceptions.SecretNotFound("discord-user secrets not specified in secrets.json.")

        identifier = self.bot.secrets["discord-user-id"]
        token = self.bot.secrets["discord-user-token"]

        if ctx.guild.get_member(identifier) is None:
            fail = utilities.Embeds.status(False)
            fail.description = "Someone is missing..."
            fail.set_footer(text="Consider inviting them?", icon_url=utilities.Icons.CROSS)
            return await ctx.reply(embed=fail)

        async with expcord.User(token) as remote:
            await remote.connect(channel)
            await remote.stream(channel)

            await asyncio.sleep(5)
            await remote.disconnect()

def setup(bot: model.Bakerbot) -> None:
    cog = Random(bot)
    bot.add_cog(cog)
