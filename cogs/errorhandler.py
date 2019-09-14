"""Handles exceptions not caught locally."""
from discord.ext import commands

class errorhandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Actual error handler."""
        if hasattr(ctx.command, "on_error"): return
        await ctx.send(str(error))
        raise error

def setup(bot): bot.add_cog(errorhandler(bot))