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
    async def render(self, ctx: commands.Context, *, query: str) -> None:
        """Render WolframAlpha's interpretation of your query."""
        async with ctx.typing():
            if (response := await Wolfram.query(query=query, formats="image", mag="3", width="1500", podindex="1")) is None:
                fail = Embeds.status(success=False, desc="WolframAlpha failed to respond.")
                return await ctx.reply(embed=fail)

            if response.success == False:
                embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
                embed.set_footer(text=f"Response time: {response.return_time:0.2f}s", icon_url=ctx.author.avatar_url)

                if response.tips:
                    tips = Regexes.escape_markdown("\n".join(response.tips))
                    embed.add_field(name="Some helpful tips that might help:", value=tips, inline=False)
                elif isinstance(response.error, dict):
                    title = "WolframAlpha encountered an error."
                    embed.add_field(name=title, value=f"{response.error['msg']}.", inline=False)
                else:
                    title = "WolframAlpha doesn't know how to render that."
                    embed.add_field(name=title, value="Try something else, perhaps?", inline=False)

                return await ctx.reply(embed=embed)

        embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
        embed.set_footer(text=f"Response time: {response.return_time:0.2f}s", icon_url=ctx.author.avatar_url)
        await ctx.send(response.pods[0]["subpods"][0]["img"]["src"])

    @commands.command()
    async def wolfram(self, ctx: commands.Context, *, query: str) -> None:
        """Make a request to WolframAlpha."""
        async with ctx.typing():
            if (response := await Wolfram.query(query=query, formats="plaintext")) is None:
                fail = Embeds.status(success=False, desc="WolframAlpha failed to respond.")
                return await ctx.reply(embed=fail)

            if response.success == False:
                embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
                embed.set_footer(text=f"Response time: {response.return_time:0.2f}s", icon_url=ctx.author.avatar_url)

                if response.tips:
                    tips = Regexes.escape_markdown("\n".join(response.tips))
                    embed.add_field(name="Some helpful tips that might help:", value=tips, inline=False)
                elif isinstance(response.error, dict):
                    title = "WolframAlpha encountered an error."
                    embed.add_field(name=title, value=f"{response.error['msg']}.", inline=False)
                else:
                    title = "WolframAlpha doesn't know how to answer your query."
                    embed.add_field(name=title, value="Try something else, perhaps?", inline=False)

                return await ctx.reply(embed=embed)

        embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
        embed.set_footer(text=f"Response time: {response.return_time:0.2f}s", icon_url=ctx.author.avatar_url)

        for pod in response.pods:
            for subpod in pod["subpods"]:
                if (value := subpod.get("plaintext", "")) != "":
                    title = subpod["title"] or pod["title"]
                    embed.add_field(name=title, value=value, inline=False)

        await ctx.reply(embed=embed)

def setup(bot): bot.add_cog(Maths(bot))
