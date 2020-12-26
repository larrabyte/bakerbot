from discord.ext import commands
import utilities
import random
import discord
import asyncio

class games(commands.Cog):
    """Bakerbot Twitch streaming coming soon, I promise!"""
    def __init__(self, bot: commands.Bot):
        self.giving = False
        self.bot = bot

    @commands.command()
    async def giveaway(self, ctx: commands.Context, *, prize: str):
        """Giveaway random prizes! Pass in a prize to display."""
        if self.giving: raise commands.CommandOnCooldown(None, 10)
        self.giving = True

        size = 5 if len(ctx.guild.members) >= 5 else len(ctx.guild.members)
        members = random.sample(ctx.guild.members, size)
        displayed = "\n".join([member.mention for member in members])
        winner = random.choice(members)

        embed = discord.Embed(title=f"Bakerbot: {ctx.author.name}'s lottery!", colour=utilities.gamingColour)
        embed.add_field(name="The Winner's Prize", value=prize, inline=False)
        embed.add_field(name="Potential Winners", value=displayed, inline=False)
        await ctx.send(embed=embed)
        await asyncio.sleep(random.randint(1, 10))

        embed = discord.Embed(title=f"Bakerbot: {ctx.author.name}'s lottery!", colour=utilities.gamingColour)
        embed.add_field(name="code is fucked and so is ur mum :point_right: :sunglasses: :point_right:", value=f"{winner} wins {prize}!", inline=False)
        await ctx.send(embed=embed)
        self.giving = False

    @giveaway.error
    async def giveawayerror(self, ctx: commands.Context, error: object):
        """Error handler for the giveaway command."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(title="Bakerbot: Lottery exception.", description="Another lottery is currently in progress, please wait.", colour=utilities.errorColour)
            await ctx.send(embed=embed)

def setup(bot): bot.add_cog(games(bot))
