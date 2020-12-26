from discord.ext import commands
import utilities
import discord
import typing

class helper(commands.Cog):
    """Bakerbot's custom helper function lives here :)"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx: commands.Context, cogname: typing.Optional[str]):
        """Bakerbot's custom help function."""
        if not cogname:
            cogs = [self.bot.cogs[name] for name in self.bot.cogs]
            embed = discord.Embed(title="Bakerbot: List of command groups.", colour=utilities.regularColour)
            embed.set_footer(text="Note: typing $help [cogname] will display available commands in that cog.")
            for cog in cogs: embed.add_field(name=cog.qualified_name, value=cog.description, inline=False)
        else:
            cog = self.bot.get_cog(cogname)
            if not cog: raise utilities.CogDoesntExist
            embed = discord.Embed(title=f"Bakerbot: List of commands in {cogname}.", colour=utilities.regularColour)
            embed.set_footer(text="Note: arguments enclosed in <> are required while [] are optional.")
            for command in cog.get_commands(): embed.add_field(name=f"{command.name} {command.signature}", value=command.help, inline=False)

        await ctx.send(embed=embed)

    @help.error
    async def helperror(self, ctx: commands.Context, error: object):
        """Error handler for the help function."""
        if isinstance(error, utilities.CogDoesntExist):
            embed = discord.Embed(title="Bakerbot: Helper exception.", description="That cog does not exist.", colour=utilities.errorColour)
            await ctx.send(embed=embed)

def setup(bot): bot.add_cog(helper(bot))
