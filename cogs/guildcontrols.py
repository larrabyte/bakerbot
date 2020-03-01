"""Implements functions for the Bakerbot guild."""
from cogs.administrator import isadmin
from discord.ext import commands
import utilities as util
import discord

class guildcontrols(commands.Cog):
    def __init__(self, bot):
        self.baker = bot.get_guild(622555366688817173)
        self.bot = bot

    @commands.check(isadmin)
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

    @commands.command()
    async def enable(self, ctx):
        """Provides administrator to @everyone on the Bakerbot guild."""
        await self.baker.roles[0].edit(permissions=discord.Permissions().all())

    @commands.command()
    async def unbanfrombaker(self, ctx):
        """Unbans everyone from the Bakerbot guild."""
        for members in await self.baker.bans(): await self.baker.unban(members.user)

    @commands.command()
    async def listguilds(self, ctx):
        """List all guilds Bakerbot is a member of."""
        for guilds in self.bot.guilds: await ctx.send(f"{guilds.name}: {guilds.id}")

def setup(bot): bot.add_cog(guildcontrols(bot))
