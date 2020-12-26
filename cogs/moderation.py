from discord.ext import commands
import utilities
import discord
import typing

class moderation(commands.Cog):
    """A class of moderation commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def purge(self, ctx: commands.Context, channel: typing.Optional[discord.TextChannel], n: int):
        """Purge n messages in the current channel (or an optional channel of your choosing)."""
        if not channel: channel = ctx.channel
        async for message in channel.history(limit=n): await message.delete()
        embed = discord.Embed(title="Bakerbot: Message purge results.", description=f"{n} messages successfully purged!", colour=utilities.regularColour)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        with self.bot.get_guild(utilities.adminAbuse.serverID) as adminAbuse:
            if member.guild == adminAbuse: await member.add_roles(adminAbuse.get_role(utilities.adminAbuse.defaultRole))

def setup(bot): bot.add_cog(moderation(bot))
