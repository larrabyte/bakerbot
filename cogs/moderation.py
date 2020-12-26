from discord.ext import commands
import discord

class moderation(commands.Cog, name="moderation"):
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

def setup(bot): bot.add_cog(moderation(bot))
