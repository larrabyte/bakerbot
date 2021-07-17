import discord.ext.commands as commands
import traceback as trace
import typing as t
import discord
import model

class Debugger(commands.Cog):
    """Provides a built-in debugger for Bakerbot."""
    def __init__(self, bot: model.Bakerbot):
        self.colours = bot.utils.Colours
        self.icons = bot.utils.Icons
        self.embeds = bot.utils.Embeds
        self.bot = bot

    @commands.is_owner()
    @commands.group(invoke_without_subcommand=True)
    async def mod(self, ctx: commands.Context):
        """The parent command for the module manager."""
        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                # There is no subcommand: inform the user about the module manager.
                summary = """Welcome to the module manager. This command group is responsible
                            for providing a front end to Bakerbot's extension loader/unloader.
                            See `$help debugger` for a full list of available subcommands."""

                footer = "Only approved users may execute module manager commands."
                embed = discord.Embed(colour=self.colours.regular, timestamp=self.embeds.now())
                embed.description = summary
                embed.set_footer(text=footer, icon_url=self.icons.info)
                await ctx.reply(embed=embed)
            else:
                # The subcommand was not valid: throw a fit.
                command = f"${ctx.command.name} {ctx.subcommand_passed}"
                summary = f"`{command}` is not a valid command."
                footer = "Try $help debugger for a full list of available subcommands."
                embed = self.embeds.status(False, summary)
                embed.set_footer(text=footer, icon_url=self.icons.cross)
                await ctx.reply(embed=embed)

    @mod.command()
    async def load(self, ctx: commands.Context, cog: str):
        """Extension loader, requires a fully qualified module name."""
        self.bot.load_extension(cog)
        embed = self.embeds.status(True, f"{cog} has been loaded.")
        await ctx.reply(embed=embed)

    @mod.command()
    async def unload(self, ctx: commands.Context, cog: str):
        """Extension unloader, requires a fully qualified module name."""
        self.bot.unload_extension(cog)
        embed = self.embeds.status(True, f"{cog} has been unloaded.")
        await ctx.reply(embed=embed)

    @mod.command()
    async def reload(self, ctx: commands.Context, cog: t.Optional[str]) -> None:
        """Extension reloader, reloads all cogs or `cog` if passed in."""
        if cog is not None:
            self.bot.reload_extension(cog)

        else: # Refresh the bot's internal state.
            self.bot.utils = self.bot.loadutils()
            self.bot.secrets = self.bot.loadsecrets()
            cache = [c for c in self.bot.cogs]

            for cogs in cache:
                name = f"cogs.{cogs.lower()}"
                self.bot.reload_extension(name)

        summary = f"{cog} has been reloaded." if cog is not None else "All modules reloaded."
        embed = self.embeds.status(True, summary)
        await ctx.reply(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Catches any exceptions thrown from commands and forwards them to Discord."""
        ex = error.original if isinstance(error, commands.CommandInvokeError) else error

        # Perform custom error handling depending on the type of exception.
        if isinstance(ex, commands.CommandNotFound) and not ctx.message.content[1].isdigit():
            reason = f"`{ctx.message.content}` is not a valid command."
            footer = f"Try $help for a list of command groups."
            fail = self.embeds.status(False, reason)
            fail.set_footer(text=footer, icon_url=self.icons.cross)
            await ctx.reply(embed=fail)

        elif isinstance(ex, commands.MissingRequiredArgument):
            reason = f"`{ex.param.name}` is a required argument that is missing."
            footer = f"Expected an argument of type {ex.param.annotation.__name__}."
            fail = self.embeds.status(False, reason)
            fail.set_footer(text=footer, icon_url=self.icons.cross)
            await ctx.reply(embed=fail)

        else: # Otherwise, we perform generic error handling.
            embed = self.embeds.status(False, "")
            embed.title = "Exception raised. See below for more information." 

            # Extract traceback information if available.
            if (traceback := ex.__traceback__) is not None:
                embed.title = "Exception raised. Traceback reads as follows:"

                for l in trace.extract_tb(traceback):
                    embed.description += f"Error occured in {l[2]}, line {l[1]}:\n"
                    embed.description += f"    {l[3]}\n"

            # Package the text/traceback data into an embed field and send it off.
            readable = str(ex) or type(ex).__name__
            embed.description += readable

            maximum = 6000 - (len(embed.title) + 6)
            if len(embed.description) > maximum:
                embed.description = embed.description[:maximum]

            embed.description = f"```{embed.description}```"
            await ctx.reply(embed=embed)

def setup(bot: model.Bakerbot) -> None:
    cog = Debugger(bot)
    bot.add_cog(cog)
