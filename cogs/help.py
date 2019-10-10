"""A cog implementing the `help` and `whoami` function."""
from cogs.administrator import admins
from discord.ext import commands
import utilities as util
import importlib
import psutil

def loadcog(bot, cogname):
    modified = cogname.replace(".py", "").replace("cogs.", "")
    return bot.get_cog(modified)

class help(commands.Cog):
    def __init__(self, bot):
        self.proc = psutil.Process()
        self.bot = bot

    @commands.command(aliases=["info"])
    async def whoami(self, ctx):
        """Who am I?"""
        embed = util.getembed("Bakerbot: Who am I?", 0xFF8C00)
        embed.add_field(name="str(author)", value="<@" + str(admins[0]) + ">", inline=True)
        
        average = str(len(self.bot.users) / len(self.bot.guilds))
        embed.add_field(name="len(servers)", value=str(len(self.bot.guilds)) + " (avg: " + average + " members/guild)", inline=True)
        embed.add_field(name="len(loadedcommands)", value=str(len(self.bot.commands)), inline=True)
        embed.add_field(name="fetch(ramusage.mb)", value=str(self.proc.memory_info().rss / 1024**2), inline=True)
        await ctx.send(embed=embed)

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