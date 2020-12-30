from discord.ext import commands
import datetime as dt
import typing as t
import discord

class Debugger(commands.Cog, name="debugger"):
    """Bakerbot's internal debugger. Home to a module injector."""
    def __init__(self, bot: commands.Bot) -> None:
        bot.loop.create_task(self.startup())
        self.bot = bot

    async def startup(self) -> None:
        """Manages any cog prerequisites."""
        await self.bot.wait_until_ready()
        self.util = self.bot.get_cog("utilities")

    def mod_embed(self, description: str, footer_text: str, success: bool) -> discord.Embed:
        """Returns a Discord Embed useful for the module command group."""
        ett = "Bakerbot: Module injector." if success else "Bakerbot: Module injector exception."
        eco = self.util.success_colour if success else self.util.error_colour
        efi = self.util.tick_icon if success else self.util.cross_icon

        embed = discord.Embed(title=ett, description=description, colour=eco, timestamp=dt.datetime.utcnow())
        embed.set_footer(text=footer_text, icon_url=efi)
        return embed

    async def command_not_found(self, ctx: commands.Context, error: object) -> None:
        """Run when on_command_error() is raised without a valid command."""
        embed = discord.Embed(title="Bakerbot: Command not found!",
                              description="Try a different command, or see $help for command groups.",
                              colour=self.util.error_colour,
                              timestamp=dt.datetime.utcnow())

        embed.set_footer(text=f"Raised by {ctx.author.name} while trying to run {ctx.message.content}.",
                         icon_url=self.util.cross_icon)

        await ctx.send(embed=embed)

    async def command_error_default(self, ctx: commands.Context, error: object) -> None:
        """Run when on_command_error() when an unknown error is encountered."""
        if str(error) == "": errstr = type(error)
        elif str(error)[-1] != "`" and str(error)[-1] != ".": errstr = f"{error}."
        else: errstr = str(error)

        embed = discord.Embed(title="Bakerbot: Unhandled exception.",
                              colour=self.util.error_colour,
                              timestamp=dt.datetime.utcnow())

        embed.add_field(name="The exception reads as follows:", value=errstr, inline=False)
        embed.set_footer(text=f"Raised by {ctx.author.name} while trying to run ${ctx.command}.", icon_url=self.util.cross_icon)
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.group(invoke_without_subcommand=True)
    async def mod(self, ctx: commands.Context) -> None:
        """Module command group fallback handler."""
        if ctx.invoked_subcommand == None:
            embed = self.mod_embed(description="Invalid subcommand passed in. See $help debugger for valid subcommands.",
                                   footer_text=f"Raised by {ctx.author.name} while trying to run {ctx.message.content}.",
                                   success=False)

            await ctx.send(embed=embed)

    @mod.command()
    async def load(self, ctx: commands.Context, cogname: str) -> None:
        """Loads a module using `cogname`."""
        self.bot.load_extension(f"cogs.{cogname}")
        embed = self.mod_embed(description=f"{cogname} successfully loaded!",
                               footer_text=f"Python import path: cogs.{cogname}",
                               success=True)

        await ctx.send(embed=embed)

    @mod.command()
    async def unload(self, ctx: commands.Context, cogname: str) -> None:
        """Unloads a module using `cogname`."""
        self.bot.unload_extension(f"cogs.{cogname}")
        embed = self.mod_embed(description=f"{cogname} successfully unloaded!",
                               footer_text=f"Python import path: cogs.{cogname}",
                               success=True)

        await ctx.send(embed=embed)

    @mod.command()
    async def reload(self, ctx: commands.Context, cogname: t.Optional[str]) -> None:
        """Reloads the `cogname` module, otherwise reloads all modules."""
        edt = f"All modules successfully reloaded!" if cogname is None else f"{cogname} successfully reloaded!"
        eft = f"{len(self.bot.cogs)} cogs now active." if cogname is None else f"Python import path: cogs.{cogname}"
        embed = self.mod_embed(description=edt, footer_text=eft, success=True)

        if cogname is None:
            cogs = [f"cogs.{names}" for names in self.bot.cogs]
            for cog in cogs: self.bot.reload_extension(cog)
        else: self.bot.reload_extension(f"cogs.{cogname}")

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: object) -> None:
        """Throws any uncaught exceptions to Discord."""
        if not ctx.command: await self.command_not_found(ctx, error)
        else: await self.command_error_default(ctx, error)
        raise error

def setup(bot): bot.add_cog(Debugger(bot))
