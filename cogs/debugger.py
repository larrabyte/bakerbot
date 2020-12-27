from discord.ext import commands
import utilities
import datetime
import discord
import typing

class debugger(commands.Cog):
    """Bakerbot's internal debugger. Home to an extension injector."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def modreload(self, ctx: commands.Context, cogname: typing.Optional[str]):
        """Reloads a passed in cog, or reloads all cogs."""
        if not cogname:
            cogname = "All"
            cogs = [f"cogs.{cog}" for cog in self.bot.cogs]
            for item in cogs: self.bot.reload_extension(item)
        else: self.bot.reload_extension(f"cogs.{cogname}")

        embed = discord.Embed(title="Bakerbot: Extension reloader.", description=f"{cogname} successfully reloaded!", colour=utilities.successColour)
        await ctx.send(embed=embed)

    @commands.command()
    async def modlist(self, ctx: commands.Context):
        """Provides the command group list."""
        coglist = "\n".join(self.bot.cogs)
        embed = discord.Embed(title="Bakerbot: Command group listing.", description=coglist, colour=utilities.regularColour)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: object):
        """Throws any uncaught exceptions to Discord."""
        if hasattr(ctx.command, "on_error"): pass
        elif not ctx.command: await self.command_not_found(ctx, error)
        else: await self.command_error_default(ctx, error)
        raise error

    async def command_not_found(self, ctx: commands.Context, error: object):
        """Run when on_command_error() is raised without a valid command."""
        embed = discord.Embed(title="Bakerbot: Command not found!", description="Try a different command, or see $help for command groups.", colour=utilities.errorColour)
        await ctx.send(embed=embed)

    async def command_error_default(self, ctx: commands.Context, error: object):
        """Run when on_command_error() when an unknown error is encountered."""
        if str(error) == "": errstr = type(error)
        else: errstr = str(error) if str(error)[-1] == "." else f"{error}."

        embed = discord.Embed(title="Bakerbot: Unhandled exception!", colour=utilities.errorColour, timestamp=datetime.datetime.utcnow())
        embed.add_field(name="The exception reads as follows:", value=errstr, inline=False)
        embed.set_footer(text=f"Raised by {ctx.author.name} while trying to run ${ctx.command}.", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

def setup(bot): bot.add_cog(debugger(bot))
