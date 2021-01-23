from libs.utilities import Embeds, Colours, Regexes
from libs.wolfram import Wolfram
from libs.models import Bakerbot
from discord.ext import commands

import discord

class Maths(commands.Cog):
    """**Experimental** WolframAlpha support."""
    def __init__(self, bot: Bakerbot):
        self.bot = bot

    @commands.command()
    async def wolfram(self, ctx: commands.Context, *, query: str) -> None:
        """Make a request to WolframAlpha."""
        async with ctx.typing():
            if (response := await Wolfram.query(query)) is None:
                fail = Embeds.status(success=False, desc="WolframAlpha failed to respond.")
                return await ctx.reply(embed=fail)

            if response.success == False:
                embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
                embed.set_footer(text="Unsuccessful response returned.", icon_url=ctx.author.avatar_url)

                if response.tips:
                    tips = Regexes.escape_markdown("\n".join(response.tips))
                    embed.add_field(name="Some helpful tips that might help:", value=tips, inline=False)
                else:
                    title = "WolframAlpha doesn't know how to answer your query."
                    embed.add_field(name=title, value="Try something else, perhaps?", inline=False)

                return await ctx.reply(embed=embed)

        embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
        embed.set_footer(text="Successful response returned.", icon_url=ctx.author.avatar_url)

        for pod in response.pods:
            subpod = pod["subpods"][0]
            if (value := subpod.get("plaintext", None)) is not None:
                if value != "": embed.add_field(name=pod["title"], value=value)

        await ctx.reply(embed=embed)

def setup(bot): bot.add_cog(Maths(bot))
