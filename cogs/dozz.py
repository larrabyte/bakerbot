from backends import sv443
import model

from discord.ext import commands
import asyncio

class Dozz(commands.Cog):
    """Made by the Big Dominic."""
    def __init__(self, bot: model.Bakerbot):
        self.bot = bot

    @commands.command()
    async def joke(self, ctx: commands.Context) -> None:
        """Get a fucking joke."""
        await ctx.send("OK, cooking up a joke.")

        async with ctx.typing():
            joke = await sv443.Backend.joke()

            if joke["type"] == "single":
                await asyncio.sleep(3)
                await ctx.send(joke["joke"])

            elif joke["type"] == "twopart":
                await ctx.send(joke["setup"])
                await asyncio.sleep(5)
                await ctx.send(joke["delivery"])

def setup(bot: model.Bakerbot) -> None:
    cog = Dozz(bot)
    bot.add_cog(cog)
