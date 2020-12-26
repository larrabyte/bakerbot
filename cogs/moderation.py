from discord.ext import commands
import utilities
import discord

class moderation(commands.Cog):
    """A class of moderation commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def purge(self, ctx: commands.Context, n: int, channel: discord.TextChannel = None):
        """Purge messages in a certain channel."""
        if not channel: channel = ctx.channel
        async for message in channel.history(limit=n):
            await message.delete()

        await ctx.send(f"{n} messages purged!")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        with self.bot.get_guild(utilities.adminAbuse.serverID) as adminAbuse:
            if member.guild == adminAbuse: await member.add_roles(adminAbuse.get_role(utilities.adminAbuse.defaultRole))

def setup(bot): bot.add_cog(moderation(bot))
