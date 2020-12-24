from discord.ext import commands

class debugger(commands.Cog):
    """Bakerbot's internal debugger. Hosts the exception handler and a Jishaku bootstrapper."""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Throws exceptions to Discord."""
        if hasattr(ctx.command, "on_error"): return
        await ctx.send(str(error))
        raise error

    @commands.is_owner()
    @commands.command()
    async def loadjsk(self, ctx):
        """Jishaku bootstrapper. Only the owner may execute this command."""
        self.bot.load_extension("jishaku")

def setup(bot): bot.add_cog(debugger(bot))
