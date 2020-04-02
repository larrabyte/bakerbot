from discord.ext import commands
from glob import glob
from helpers import *

class debugger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Throws exceptions to Discord."""
        if hasattr(ctx.command, "on_error"): return
        await ctx.send(str(error))
        raise error

    @commands.command(aliases=["mod"])
    async def module(self, ctx, action: str, module: str=None):
        """Loads, unloads and reloads modules."""
        if action == "load" and module: 
            self.bot.load_extension(module)
            await ctx.send(f"{module} loaded.")
        elif action == "unload" and module:
            self.bot.unload_extension(module)
            await ctx.send(f"{module} unloaded.")
        elif action == "reload" and module:
            self.bot.reload_extension(module)
            await ctx.send(f"{module} reloaded.")
        elif action == "reloadall":
            for files in glob("cogs/*.py"): self.bot.reload_extension(file2ext(files))
            await ctx.send("All modules reloaded.")

def setup(bot): bot.add_cog(debugger(bot))
