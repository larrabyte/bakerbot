from discord.ext import commands
import utilities
import discord

class helper(commands.Cog):
    """Implements the help function."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx: commands.Context, cogname: str = None):
        """Bakerbot's custom help function."""
        if not cogname:
            cogs = [self.bot.cogs[name] for name in self.bot.cogs]
            embed = discord.Embed(title="Bakerbot: List of command groups.", colour=utilities.regularColour)
            for cog in cogs: embed.add_field(name=cog.qualified_name, value=cog.description, inline=False)
        else:
            embed = discord.Embed(title=f"Bakerbot: List of commands in {cogname}.", colour=utilities.regularColour)
            for commands in self.bot.get_cog(cogname).get_commands(): embed.add_field(name=commands.name, value=commands.help, inline=False)

        await ctx.send(embed=embed)

def setup(bot): bot.add_cog(helper(bot))
