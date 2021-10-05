import utilities
import model

from discord.ext import commands

class Debugger(commands.Cog):
    """Provides a built-in debugger for Bakerbot."""
    def __init__(self, bot: model.Bakerbot):
        self.bot = bot

    @commands.is_owner()
    @commands.group(invoke_without_subcommand=True)
    async def mod(self, ctx: commands.Context):
        """The parent command for the module manager."""
        summary = ("You've encountered Bakerbot's module manager! "
                   "See `$help debugger` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @mod.command()
    async def load(self, ctx: commands.Context, cog: str):
        """Loads a command group."""
        self.bot.load_extension(cog)
        embed = utilities.Embeds.status(True)
        embed.description = f"{cog} has been loaded."
        await ctx.reply(embed=embed)

    @mod.command()
    async def unload(self, ctx: commands.Context, cog: str):
        """Unloads a command group."""
        self.bot.unload_extension(cog)
        embed = utilities.Embeds.status(True)
        embed.description = f"{cog} has been unloaded."
        await ctx.reply(embed=embed)

    @mod.command()
    async def reload(self, ctx: commands.Context, cog: str | None) -> None:
        """Reloads `cog` if specified, otherwise refreshes the bot's internal state."""
        if cog is not None:
            self.bot.reload_extension(cog)
            summary = f"{cog} has been reloaded."
        else:
            self.bot.reload()
            summary = "All modules reloaded."

        embed = utilities.Embeds.status(True)
        embed.description = summary
        await ctx.reply(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Catches any exceptions thrown from commands and forwards them to Discord."""
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        # Perform custom error handling depending on the type of exception.
        if ctx.message.content[1].isdigit():
            pass

        elif isinstance(error, commands.CommandNotFound):
            command = ctx.message.content.split(" ")[0]
            fail = utilities.Embeds.status(False, description=f"`{command}` is not a valid command.")
            fail.set_footer(text="Try $help for a list of command groups.", icon_url=utilities.Icons.CROSS)
            await ctx.reply(embed=fail)

        elif isinstance(error, commands.MissingRequiredArgument):
            prefix = f"{ctx.command.full_parent_name} " if ctx.command.parent else ""
            template = f"{prefix}{ctx.command.name} {ctx.command.signature}"

            fail = utilities.Embeds.status(False)
            fail.description = f"`{error.param.name}` (type {error.param.annotation.__name__}) is a required argument that is missing.\n"
            fail.set_footer(text=f"Command signature: {template}", icon_url=utilities.Icons.CROSS)
            await ctx.reply(embed=fail)

        elif isinstance(error, (commands.CheckFailure, commands.CheckAnyFailure)):
            fail = utilities.Embeds.status(False)
            fail.description = "The current context does not support execution of this command."
            fail.set_footer(text=f"Exception type: {error.__module__}.{error.__class__.__name__}.", icon_url=utilities.Icons.CROSS)
            await ctx.reply(embed=fail)

        else:
            embed = utilities.Embeds.error(error)
            await ctx.reply(embed=embed)

def setup(bot: model.Bakerbot) -> None:
    cog = Debugger(bot)
    bot.add_cog(cog)
