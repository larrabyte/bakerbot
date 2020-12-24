from discord.ext import commands
from utilities import *

class debugger(commands.Cog):
    """Bakerbot's internal debugger. Hosts the exception handler and a Jishaku bootstrapper."""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Throws exceptions to Discord."""
        if hasattr(ctx.command, "on_error"): return
        embed = getembed("Bakerbot: Unhandled exception!", f"Raised by {ctx.author.mention} while using ${ctx.command}.", 0xFF0000)
        embed.add_field(name=f"{error}.", value="Try again with different arguments or contact the bot author for help.", inline=False)
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command()
    async def loadjsk(self, ctx):
        """Jishaku bootstrapper. Only the owner may execute this command."""
        self.bot.load_extension("jishaku")

def setup(bot): bot.add_cog(debugger(bot))
