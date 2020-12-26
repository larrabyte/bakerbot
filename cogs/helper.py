from discord.ext import commands
import utilities
import discord
import typing

class helper(commands.Cog):
    """Implements the help function."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx: commands.Context, cogname: typing.Optional[str]):
        """Bakerbot's custom help function."""
        if not cogname:
            cogs = [self.bot.cogs[name] for name in self.bot.cogs]
            embed = discord.Embed(title="Bakerbot: List of command groups.", colour=utilities.regularColour)
            for cog in cogs: embed.add_field(name=cog.qualified_name, value=cog.description, inline=False)
        else:
            cog = self.bot.get_cog(cogname)
            if not cog: raise commands.BadArgument()
            embed = discord.Embed(title=f"Bakerbot: List of commands in {cogname}.", colour=utilities.regularColour)
            for command in cog.get_commands(): embed.add_field(name=f"{command.name} {command.signature}", value=command.help, inline=False)

        await ctx.send(embed=embed)

    @help.error
    async def helperror(self, ctx: commands.Context, error: object):
        """Error handler for the help function."""
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="Bakerbot: Helper exception.", description="That cog does not exist.", colour=utilities.errorColour)
            await ctx.send(embed=embed)

def setup(bot): bot.add_cog(helper(bot))
