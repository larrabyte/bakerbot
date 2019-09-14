"""Implements functions for the Bakerbot guild."""
from discord.ext import commands
import utilities as util
import discord

class guildcontrols(commands.Cog):
    def __init__(self, bot):
        self.baker = bot.get_guild(util.guilds[2])
        self.bot = bot

    @commands.command()
    async def createguild(self, ctx):
        """Make a Bakerbot guild. Use when someone utterly destroys another one."""
        self.baker = await self.bot.create_guild(name="Bakerbot Guild", region=discord.VoiceRegion.sydney)
        invite = await self.baker.text_channels[0].create_invite(max_age=0, max_uses=0, temporary=False, unique=True)
        await ctx.send(invite.url)

    @commands.command()
    async def makeinvite(self, ctx):
        """Create an invite to the Bakerbot guild."""
        if len(self.baker.text_channels) == 0: await self.baker.create_text_channel("general")
        invite = await self.baker.text_channels[0].create_invite(max_age=0, max_uses=0, temporary=False, unique=True)
        await ctx.send(invite.url)

def setup(bot): bot.add_cog(guildcontrols(bot))
