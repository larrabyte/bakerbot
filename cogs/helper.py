from discord.ext import commands
from random import randint
from utilities import *

class helper(commands.Cog):
    """Implements the help function."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["helpme"])
    async def help(self, ctx, cogname: str=None):
        """Bakerbot's custom help function. Optionally, takes in `cogname`."""
        if not cogname:
            cogs = [self.bot.cogs[name] for name in self.bot.cogs]
            embed = getembed("Bakerbot: List of command groups.")
            for cog in cogs: embed.add_field(name=cog.qualified_name, value=cog.description, inline=False)
        else:
            embed = getembed(f"Bakerbot: List of commands in {cogname}.")
            for commands in self.bot.get_cog(cogname).get_commands():
                embed.add_field(name=commands.name, value=commands.help, inline=False)

        await ctx.send(embed=embed)

def setup(bot): bot.add_cog(helper(bot))
