"""Adds a module reloading function and an error handler."""
from discord.ext import commands
import utilities as util

class debugging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Throws exceptions to Discord."""
        if hasattr(ctx.command, "on_error"): return
        await ctx.send(str(error))
        raise error

    @commands.command(aliases=["mod"])
    async def module(self, ctx, action, module: str=None):
        """Loads, unloads and reloads modules."""
        if action == "load" and module: self.bot.load_extension(module)
        elif action == "unload" and module: self.bot.unload_extension(module)
        elif action == "reload" and module: self.bot.reload_extension(module)
        elif action == "reloadall":
            for things in util.fetchcogs(): self.bot.reload_extension(util.getcogname(things))

def setup(bot): bot.add_cog(debugging(bot))