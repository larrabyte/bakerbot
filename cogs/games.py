from discord.ext import commands
from utilities import *
from random import *
import discord
import asyncio

class games(commands.Cog):
    """This cog hosts some fun games!"""
    def __init__(self, bot):
        self.giving = False
        self.bot = bot

    @commands.command()
    async def giveaway(self, ctx, *, prize: str):
        """Giveaway random prizes! Pass in a prize to display."""
        if self.giving: raise commands.CommandOnCooldown(None, 5)
        self.giving = True

        size = 5 if len(ctx.guild.members) >= 5 else len(ctx.guild.members)
        members = "\n".join([member.mention for member in sample(ctx.guild.members, size)])
        embed = getembed(f"Bakerbot: The lottery!", "sponsored by the pharmaceutical industry\ntime to find winner: approx. 5s", ECONOMYCOLOUR)
        embed.add_field(name="Winner's Prize", value=f"From {ctx.author.name}: {prize}", inline=False)
        embed.add_field(name="Potential Winners", value=members, inline=False)
        await ctx.send(embed=embed)
        await asyncio.sleep(5)

        winner = choice(members.split("\n"))
        embed = getembed("Bakerbot: The lottery!", "sponsored by the pharmaceutical industry", ECONOMYCOLOUR)
        embed.add_field(name="code is fucked and so is ur mum :point_right: :sunglasses: :point_right:", value=f"{winner} wins {prize}!")
        await ctx.send(embed=embed)
        self.giving = False

    @giveaway.error
    async def giveawayerror(self, ctx, error):
        """Error handler for the giveaway command."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = getembed("Bakerbot: Lottery exception.", f"Raised by {ctx.author.name} whilst trying to start a new lottery.", ERRORCOLOUR)
            embed.add_field(name="Unable to start new lottery.", value="Another lottery is currently in progress, please wait.", inline=False)
            await ctx.send(embed=embed)
        else: raise error

def setup(bot): bot.add_cog(games(bot))
