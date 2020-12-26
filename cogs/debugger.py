from discord.ext import commands
import utilities
import discord

class debugger(commands.Cog):
    """Bakerbot's internal debugger. Home to an extension injector."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def inject(self, ctx: commands.Context, cogname: str):
        """Injects an extension into Bakerbot."""
        self.bot.load_extension(cogname)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: object):
        """Throws any uncaught exceptions to Discord."""
        if hasattr(ctx.command, "on_error"): raise error
        elif not ctx.command: await self.command_not_found(ctx, error)
        else: await self.command_error_default(ctx, error)

    async def command_not_found(self, ctx: commands.Context, error: object):
        """Run when on_command_error() is raised without a valid command."""
        embed = discord.Embed(title="Bakerbot: Command not found!", description="Try a different command, or see $help for command groups.", colour=utilities.errorColour)
        await ctx.send(embed=embed)

    async def command_error_default(self, ctx: commands.Context, error: object):
        """Run when on_command_error() when an unknown error is encountered."""
        errstr = str(error) if str(error)[-1] == "." else f"{error}."
        embed = discord.Embed(title="Bakerbot: Unhandled exception!", colour=utilities.errorColour)
        embed.add_field(name="The exception reads as follows:", value=errstr, inline=False)
        embed.set_footer(text=f"Raised by {ctx.author.name} while trying to run ${ctx.command}.")
        await ctx.send(embed=embed)

def setup(bot): bot.add_cog(debugger(bot))
