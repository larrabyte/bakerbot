from discord.ext import commands
from importlib import *
from utilities import *
import psutil

class helper(commands.Cog):
    """Implements the help function."""

    def __init__(self, bot):
        self.proc = psutil.Process()
        self.bot = bot

    def getcog(self, cogname: str):
        return self.bot.get_cog(cogname)

    @commands.command(aliases=["helpme"])
    async def help(self, ctx, cogname: str=None):
        """Help function! Optionally takes in `cogname`."""
        modules = [self.getcog(extstrip(ext)) for ext in self.bot.extensions]

        if cogname:
            embed = getembed(f"Bakerbot: List of commands in {cogname}.", 0x7000A8)
            for commands in self.getcog(cogname).get_commands(): embed.add_field(name=commands.name, value=commands.help, inline=False)
        else:
            embed = getembed("Bakerbot: List of command groups.", 0x7000A8)
            for mod in modules: embed.add_field(name=mod.qualified_name, value=mod.__doc__, inline=False)

        await ctx.send(embed=embed)

def setup(bot): bot.add_cog(helper(bot))
