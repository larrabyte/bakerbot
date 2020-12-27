from discord.ext import commands
import utilities
import datetime
import discord
import typing

class debugger(commands.Cog):
    """Bakerbot's internal debugger. Home to a module injector."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.is_owner()
    @commands.group(invoke_without_subcommand=True)
    async def mod(self, ctx: commands.Context):
        """Module command group fallback handler."""
        if ctx.invoked_subcommand == None:
            embed = discord.Embed(title="Bakerbot: Module injector exception.", description="Invalid subcommand passed in. See $help debugger for valid subcommands.", colour=utilities.errorColour, timestamp=datetime.datetime.utcnow())
            embed.set_footer(text=f"Raised by {ctx.author.name} while trying to run {ctx.message.content}.", icon_url=utilities.crossMark)
            await ctx.send(embed=embed)

    @mod.command()
    async def load(self, ctx: commands.Context, cogname: str):
        """Loads a module using `cogname`."""
        self.bot.load_extension(f"cogs.{cogname}")
        embed = discord.Embed(title="Bakerbot: Module injector.", description=f"{cogname} successfully loaded!", colour=utilities.successColour, timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=f"Python import path: cogs.{cogname}", icon_url=utilities.tickMark)
        await ctx.send(embed=embed)

    @mod.command()
    async def unload(self, ctx: commands.Context, cogname: str):
        """Unloads a module using `cogname`."""
        self.bot.unload_extension(f"cogs.{cogname}")
        embed = discord.Embed(title="Bakerbot: Module injector.", description=f"{cogname} successfully unloaded!", colour=utilities.successColour, timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=f"Python import path: cogs.{cogname}", icon_url=utilities.tickMark)
        await ctx.send(embed=embed)

    @mod.command()
    async def reload(self, ctx: commands.Context, cogname: typing.Optional[str]):
        """Reloads the `cogname` module, otherwise reloads all modules."""
        if not cogname:
            cogs = [f"cogs.{names}" for names in self.bot.cogs]
            for cog in cogs: self.bot.reload_extension(cog)
            embed = discord.Embed(title="Bakerbot: Module injector.", description=f"All modules successfully reloaded!", colour=utilities.successColour, timestamp=datetime.datetime.utcnow())
            embed.set_footer(text=f"{len(cogs)} cogs now active.", icon_url=utilities.tickMark)
        else:
            self.bot.reload_extension(f"cogs.{cogname}")
            embed = discord.Embed(title="Bakerbot: Module injector.", description=f"{cogname} successfully reloaded!", colour=utilities.successColour, timestamp=datetime.datetime.utcnow())
            embed.set_footer(text=f"Python import path: cogs.{cogname}", icon_url=utilities.tickMark)

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
        embed = discord.Embed(title="Bakerbot: Command not found!", description="Try a different command, or see $help for command groups.", colour=utilities.errorColour, timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=f"Raised by {ctx.author.name} while trying to run {ctx.message.content}.", icon_url=utilities.crossMark)
        await ctx.send(embed=embed)

    async def command_error_default(self, ctx: commands.Context, error: object):
        """Run when on_command_error() when an unknown error is encountered."""
        if str(error) == "": errstr = type(error)
        else: errstr = str(error) if str(error)[-1] == "." else f"{error}."

        embed = discord.Embed(title="Bakerbot: Unhandled exception.", colour=utilities.errorColour, timestamp=datetime.datetime.utcnow())
        embed.add_field(name="The exception reads as follows:", value=errstr, inline=False)
        embed.set_footer(text=f"Raised by {ctx.author.name} while trying to run ${ctx.command}.", icon_url=utilities.crossMark)
        await ctx.send(embed=embed)

def setup(bot): bot.add_cog(debugger(bot))
