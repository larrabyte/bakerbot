from libs.utilities import Embeds, Colours, Icons
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
        # Validate the passed in query and create a formatted error message if not.
        if query is None:
            return Embeds.status(success=False, desc="WolframAlpha failed to respond.")

        if not query.success or query.pods is None:
            embed = discord.Embed(colour=Colours.failure, timestamp=Embeds.now())
            footer = f"WolframAlpha took {query.timing:0.2f}s to respond."
            embed.set_footer(text=footer, icon_url=Icons.cross)

            if query.tips:
                text = "WolframAlpha couldn't answer that query.\nSome helpful tips that might help:"
                embed.add_field(name=text, value=query.formattedtips, inline=False)
            elif query.error:
                title = "WolframAlpha encountered an error."
                text = f"{query.errmsg}: [Click here for the raw API request.]({query.link})"
                embed.add_field(name=title, value=text, inline=False)
            else:
                title = "WolframAlpha couldn't answer your query."
                text = f"Try something else, perhaps?\n[Click here for the raw API request.]({query.link})"
                embed.add_field(name=title, value=text, inline=False)

            return embed

        # If the query was successful.
        return None

    @commands.command(aliases=["wolfram"])
    async def wa(self, ctx: commands.Context, *, query: str) -> None:
        """Generic WolframAlpha. Ask anything you want!"""
        async with ctx.typing():
            response = await Wolfram.query(query=query, formats="plaintext")
            if (check := self.checkquery(query=response)) is not None:
                return await ctx.send(embed=check)

        embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
        embed.set_footer(text=f"WolframAlpha took {response.timing:0.2f}s to respond.",
                         icon_url=ctx.author.avatar_url)

        for pod in response.pods:
            if (text := "\n".join([subpod.plaintext for subpod in pod.subpods if subpod.plaintext is not None and subpod.title == pod.title])) != "":
                embed.add_field(name=string.capwords(pod.title), value=text if len(text) < 1024 else f"{text[0:1021]}...", inline=False)

            for subpod in pod.subpods:
                if (text := subpod.plaintext) is not None and subpod.title != pod.title:
                    embed.add_field(name=string.capwords(subpod.title), value=text, inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["wolfimages"])
    async def waimages(self, ctx: commands.Context, *, query: str) -> None:
        """Generic WolframAlpha, but it spits out images instead of text."""
        async with ctx.typing():
            response = await Wolfram.query(query=query, formats="image", mag="3", width="1500")
            if (check := self.checkquery(query=response)) is not None:
                return await ctx.send(embed=check)

        for pod in response.pods:
            for subpod in pod.subpods:
                if (image := subpod.image) is not None:
                    await ctx.send(image)

    @commands.command(aliases=["render"])
    async def warender(self, ctx: commands.Context, *, query: str) -> None:
        """Spits out what WolframAlpha thought your query was. Useful for rendering equations."""
        async with ctx.typing():
            response = await Wolfram.query(query=query, formats="image", mag="3", width="1500", podindex="1")
            if (check := self.checkquery(query=response)) is not None:
                return await ctx.send(embed=check)

        if (inputpod := next((pod for pod in response.pods if pod.title == "Input"), None)) is None:
            fail = Embeds.status(success=False, desc="Couldn't find a rendered pod.")
            return await ctx.send(embed=fail)

        await ctx.send(inputpod.subpods[0].image)

    @commands.command(aliases=["solve"])
    async def wasteps(self, ctx: commands.Context, *, query: str) -> None:
        """Provide step-by-step solutions to the query passed in. Useful for solving equations."""
        async with ctx.typing():
            response = await Wolfram.query(query=query, formats="image", mag="3", width="1500", podstate="Step-by-step+solution")
            if (check := self.checkquery(query=response)) is not None:
                return await ctx.send(embed=check)

        for pod in response.pods:
            for subpod in pod.subpods:
                if subpod.title == "Possible intermediate steps":
                    return await ctx.send(subpod.image)

        # If we're at this point in code, there were no step-by-step pods found.
        fail = Embeds.status(success=False, desc="No step-by-step solutions found.")
        await ctx.send(embed=fail)

def setup(bot): bot.add_cog(Maths(bot))
