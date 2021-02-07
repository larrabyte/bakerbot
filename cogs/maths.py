from libs.utilities import Embeds, Colours, Icons, Regexes
from libs.wolfram import Wolfram, Query
from libs.models import Bakerbot
from discord.ext import commands

import typing as t
import discord
import string

class Maths(commands.Cog):
    """Houses an API wrapper for WolframAlpha (with unlimited requests!)."""
    def __init__(self, bot: Bakerbot):
        self.bot = bot

    def checkquery(self, query: Query) -> t.Optional[discord.Embed]:
        # Validate the passed in query (return an Embed if checks fail).
        if query is None or query.pods is None:
            return Embeds.status(success=False, desc="WolframAlpha failed to respond.")

        if query.success == False:
            embed = discord.Embed(colour=Colours.failure, timestamp=Embeds.now())
            footer = f"WolframAlpha took {query.return_time:0.2f}s to respond."
            embed.set_footer(text=footer, icon_url=Icons.cross)

            if query.tips:
                tips = Regexes.escape_markdown("\n".join(query.tips))
                text = "WolframAlpha couldn't answer that query.\nSome helpful tips that might help:"
                embed.add_field(name=text, value=tips, inline=False)
            elif isinstance(query.error, dict):
                title = "WolframAlpha encountered an error."
                embed.add_field(name=title, value=f"{response.error['msg']}.", inline=False)
            else:
                title = "WolframAlpha couldn't answer that query."
                text = f"Try something else, perhaps?\n[Click here for the raw API request.]({query.link})"
                embed.add_field(name=title, value=text, inline=False)

            return embed

        # If the query was successful.
        return None

    @commands.command()
    async def render(self, ctx: commands.Context, *, query: str) -> None:
        """Render WolframAlpha's interpretation of your query."""
        async with ctx.typing():
            response = await Wolfram.query(query=query, formats="image", mag="3", width="1500", podindex="1")
            if (check := self.checkquery(query=response)) is not None:
                return await ctx.send(embed=check)

        if (inputpod := next((pod for pod in response.pods if pod["id"] == "Input"), None)) is None:
            fail = Embeds.status(success=False, desc="Couldn't find a rendered pod.")
            return await ctx.send(embed=fail)

        await ctx.send(inputpod["subpods"][0]["img"]["src"])

    @commands.command()
    async def solve(self, ctx: commands.Context, *, query: str) -> None:
        """Provide step-by-step solutions to the query passed in."""
        async with ctx.typing():
            response = await Wolfram.query(query=query, formats="image", mag="3", width="1500")
            if (check := self.checkquery(query=response)) is not None:
                return await ctx.send(embed=check)

        for pod in response.pods:
            for subpod in pod["subpods"]:
                if subpod["title"] == "Possible intermediate steps":
                    return await ctx.send(subpod["img"]["src"])

        # If we're at this point in code, there were no step-by-step pods found.
        fail = Embeds.status(success=False, desc="No step-by-step solutions found.")
        await ctx.send(embed=fail)

    @commands.command()
    async def wolfram(self, ctx: commands.Context, *, query: str) -> None:
        """Generic WolframAlpha. Ask anything you want!"""
        async with ctx.typing():
            response = await Wolfram.query(query=query, formats="plaintext")
            if (check := self.checkquery(query=response)) is not None:
                return await ctx.send(embed=check)

        embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
        embed.set_footer(text=f"WolframAlpha took {response.return_time:0.2f}s to respond.",
                         icon_url=ctx.author.avatar_url)

        for pod in response.pods:
            for subpod in pod["subpods"]:
                if (value := subpod.get("plaintext", "")) != "":
                    if len(value) > 1024:
                        value = f"{value[0:1021]}..."

                    title = string.capwords(subpod["title"] or pod["title"])
                    embed.add_field(name=title, value=value, inline=False)

        await ctx.send(embed=embed)

def setup(bot): bot.add_cog(Maths(bot))
