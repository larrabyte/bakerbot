from libs.utilities import Embeds, Colours, Icons
from libs.models import Bakerbot
from discord.ext import commands

import traceback as trace
import logging as log
import typing as t
import discord

class Debugger(commands.Cog):
    """Provides a built-in debugger for Bakerbot."""
    def __init__(self, bot: Bakerbot) -> None:
        self.bot = bot

    @commands.is_owner()
    @commands.group(invoke_without_subcommand=True)
    async def mod(self, ctx: commands.Context) -> None:
        """The parent command for the module manager."""
        if ctx.invoked_subcommand is None:
            # Since there was no subcommand, inform the user about the module manager and its subcommands.
            desc = ("Welcome to the module manager. This command group is responsible for providing "
                    "a front end to Bakerbot's extension loading, unloading and reloading functions.\n"
                    "See `$help debugger` for a full list of available subcommands.")

            embed = discord.Embed(description=desc, colour=Colours.regular, timestamp=Embeds.now())
            embed.set_footer(text="Only approved users may execute module manager commands.", icon_url=Icons.info)
            await ctx.send(embed=embed)

    @mod.command()
    async def load(self, ctx: commands.Context, cogname: str) -> None:
        """Extension loader. Pass in `cogname` to load a cog."""
        self.bot.load_extension(f"cogs.{cogname}")
        embed = Embeds.status(success=True, desc=f"{cogname} has been loaded.")
        await ctx.send(embed=embed)

    @mod.command()
    async def unload(self, ctx: commands.Context, cogname: str) -> None:
        """Extension unloader. Pass in `cogname` to unload a cog."""
        self.bot.unload_extension(f"cogs.{cogname}")
        embed = Embeds.status(success=True, desc=f"{cogname} has been unloaded.")
        await ctx.send(embed=embed)

    @mod.command()
    async def reload(self, ctx: commands.Context, cogname: t.Optional[str]) -> None:
        """Extension reloader. Reloads all cogs or `cogname` if passed in."""
        if cogname is None:
            cogs = [f"cogs.{names.lower()}" for names in self.bot.cogs]
            for cog in cogs: self.bot.reload_extension(cog)
        else: self.bot.reload_extension(f"cogs.{cogname}")

        desc = "All modules reloaded." if cogname is None else f"{cogname} has been reloaded."
        embed = Embeds.status(success=True, desc=desc)
        await ctx.send(embed=embed)

    @mod.command()
    async def running(self, ctx: commands.Context) -> None:
        """Get a list of the currently running cogs."""
        # Get a formatted string of the cog objects (<Cog object at 0xFFFFFFFF>).
        formatted = "\n".join([str(self.bot.cogs[name]) for name in self.bot.cogs])
        embed = discord.Embed(title="Currently running cogs:",
                              description=f"```{formatted}```",
                              colour=Colours.regular,
                              timestamp=Embeds.now())

        embed.set_footer(text=f"{len(self.bot.cogs)} cogs active.", icon_url=Icons.info)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        # Prints some debug information to the console.
        print(f"Connected to Discord (latency: {int(self.bot.latency * 1000)}ms).")
        await self.bot.change_presence(activity=discord.Game("with the API."))

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: object) -> None:
        # Catch our exception, perform some Discord magic and send it to the log file.
        exobj = error.original if isinstance(error, commands.CommandInvokeError) else error
        log.exception("Exception raised!", exc_info=exobj)

        # Perform custom error handling depending on the type of exception.
        if isinstance(exobj, commands.CommandNotFound):
            if (ctx.message.content[1]).isdigit(): return
            fail = Embeds.status(success=False, desc=f"`{ctx.message.content}` is not a valid command.")
            fail.set_footer(text="Try $help for a list of command groups.", icon_url=Icons.cross)
            return await ctx.send(embed=fail)
        if isinstance(exobj, commands.MissingRequiredArgument):
            fail = Embeds.status(success=False, desc=f"`{exobj.param.name}` is a required argument that is missing.")
            fail.set_footer(text=f"Expected an argument of type {exobj.param.annotation.__name__}.", icon_url=Icons.cross)
            return await ctx.send(embed=fail)

        # Otherwise, we perform generic error handling.
        embed = Embeds.status(success=False, desc=None)
        embed.title = "Exception raised. See below for more information." 
        embed.description = ""

        # Extract traceback information if available.
        if exobj.__traceback__ is not None:
            embed.title = "Exception raised. Traceback reads as follows:"
            tb = trace.extract_tb(exobj.__traceback__)
            embed.description += "".join([f"Error occured in {l[2]}, line {l[1]}:\n   {l[3]}\n" for l in tb])

        # Package the text/traceback data into an embed field and send it off.
        if str(exobj) != "": embed.description += str(exobj)
        else: embed.description += type(exobj).__name__
        embed.description = f"```{embed.description}```"
        await ctx.send(embed=embed)

def setup(bot): bot.add_cog(Debugger(bot))
