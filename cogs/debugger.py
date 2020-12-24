from discord.ext import commands
from utilities import *

class debugger(commands.Cog):
    """Bakerbot's internal debugger. Hosts the exception handler and a Jishaku bootstrapper."""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Throws any uncaught exceptions to Discord."""
        if hasattr(ctx.command, "on_error"): return
        footer = f"Raised by {ctx.author.name} while using ${ctx.command}." if ctx.command else f"Raised by {ctx.author.name} while trying to use a non-existent command."
        errstr = str(error) if str(error)[-1] == "." else f"{error}."

        embed = getembed("Bakerbot: Unhandled exception!", footer, 0xFF0000)
        embed.add_field(name=errstr, value="Try again with different arguments or contact the bot author for help.", inline=False)
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command()
    async def jskswitch(self, ctx):
        """Bootstraps or unloads Jishaku through a simple self.bot() call."""
        if self.bot.cogs["jishaku"]:
            self.bot.unload_extension("jishaku")
            await ctx.send("Jishaku debugger disabled.")
        else:
            self.bot.load_extension("jishaku")
            await ctx.send("Jishaku debugger enabled.")

def setup(bot): bot.add_cog(debugger(bot))
