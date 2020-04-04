from discord.ext import commands
import subprocess
import discord

class extern(commands.Cog):
    """Implements an interface with external applications."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def quote(self, ctx):
        """Return a quote from `fortune`."""
        output = subprocess.run("bash -c fortune", encoding="utf-8", capture_output=True)
        await ctx.send(output.stdout)

def setup(bot): bot.add_cog(extern(bot))
