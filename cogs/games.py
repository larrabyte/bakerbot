from discord.ext import commands
from utilities import *
from random import *
import discord
import asyncio

class games(commands.Cog):
    """This cog hosts some fun games!"""

    def __init__(self, bot):
        self.defaultprizes = ["$-1", "shares in an African mining company", "a 1992 Toyota Hiace", "conversion to Islam",
                              "death via thigh compression", "free v-card", "penis", "vagina", "membership to the pen15 club",
                              "loss of bodily fluids", "multiple organ failure", "someone shitting on your car", "cringe"]

        self.giving = False
        self.bot = bot

    @commands.command()
    async def giveaway(self, ctx, *, prize: str=None):
        """Giveaway random prizes! Pass in a string to display."""
        if self.giving: raise GiveawayException("please wait!")

        self.giving = True
        members = "\n".join([member.mention for member in sample(ctx.guild.members, 5)])
        embed = getembed(f"The Bakerbot Lottery!", 0xFF8C00, "sponsored by the pharmaceutical industry")

        if not prize: prize = choice(self.defaultprizes)
        embed.add_field(name="Winner's Prize", value=prize, inline=False)
        embed.add_field(name="Potential Winners", value=members, inline=False)
        await ctx.send(embed=embed)
        await ctx.send("now performing extremely complicated math to find ourselves a winner winner chicken dinner")
        await asyncio.sleep(15)

        winner = choice(members.split("\n"))
        embed = getembed("The Bakerbot Lottery!", 0xFF8C00, "sponsored by the pharmaceutical industry")
        embed.add_field(name="code is fucked and so is ur mum :point_right: :sunglasses: :point_right:", value=f"{winner} wins {prize}!")
        await ctx.send(embed=embed)
        self.giving = False

def setup(bot): bot.add_cog(games(bot))
