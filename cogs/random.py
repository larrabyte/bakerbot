import utilities
import model

from discord.ext import commands
import asyncio

class Random(commands.Cog):
    """Random ideas that I come up with every now and again."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    @commands.group(invoke_without_subcommand=True, aliases=["discord"])
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

def setup(bot: model.Bakerbot) -> None:
    cog = Random(bot)
    bot.add_cog(cog)
