from discord.ext import commands
import utilities
import random
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
        members = "\n".join([member.mention for member in random.sample(ctx.guild.members, size)])
        embed = discord.Embed(title=f"Bakerbot: {ctx.author.mention}'s lottery!", colour=utilities.economyColour)
        embed.add_field(name="Winner's Prize", value=f"From {ctx.author.name}: {prize}", inline=False)
        embed.add_field(name="Potential Winners", value=members, inline=False)
        await ctx.send(embed=embed)
        await asyncio.sleep(10)

        winner = random.choice(members.split("\n"))
        embed = discord.Embed(title=f"Bakerbot: {ctx.author.mention}'s lottery!", colour=utilities.economyColour)
        embed.add_field(name="code is fucked and so is ur mum :point_right: :sunglasses: :point_right:", value=f"{winner} wins {prize}!", inline=False)
        await ctx.send(embed=embed)
        self.giving = False

    @giveaway.error
    async def giveawayerror(self, ctx, error):
        """Error handler for the giveaway command."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(title="Bakerbot: Lottery exception.", colour=utilities.errorColour)
            embed.add_field(name="Unable to start new lottery.", value="Another lottery is currently in progress, please wait.", inline=False)
            await ctx.send(embed=embed)

def setup(bot): bot.add_cog(games(bot))
