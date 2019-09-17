"""A cog implementing the `help` function."""
from discord.ext import commands
import utilities as util
import importlib

def loadcog(bot, cogname):
    modified = cogname.replace(".py", "").replace("cogs.", "")
    return bot.get_cog(modified)

class help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["helpme"])
    async def help(self, ctx, cogname: str=None):
        """Help function. Optionally, takes in `cogname`."""
        embed = util.getembed("Bakerbot: Help menu.", 0xFF8C00)
        modules = [(importlib.import_module(util.getcogname(cogs)), util.getcogname(cogs)) for cogs in util.fetchcogs()]

        if cogname:
            cog = loadcog(self.bot, cogname)
            for command in cog.get_commands(): embed.add_field(name=str(command), value=command.help, inline=False)
        else:
            for mods in modules: embed.add_field(name=mods[1], value=mods[0].__doc__, inline=False)

        await ctx.send(embed=embed)

def setup(bot): bot.add_cog(help(bot))