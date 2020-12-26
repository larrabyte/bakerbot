from discord.ext import commands
import utilities
import discord

class debugger(commands.Cog):
    """Bakerbot's internal debugger. Home to an extension injector."""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Throws any uncaught exceptions to Discord."""
        if hasattr(ctx.command, "on_error"): raise error
        if not ctx.command: await self.command_not_found(ctx, error)
        else:
            errstr = str(error) if str(error)[-1] == "." else f"{error}."
            embed = discord.Embed("Bakerbot: Unhandled exception!", f"Raised by {ctx.author.name} while using ${ctx.command}.", colour=utilities.errorColour)
            embed.add_field(name=errstr, value="Try again with different arguments or contact the bot author for help.", inline=False)
            await ctx.send(embed=embed)

    async def command_not_found(self, ctx, error):
        """Run when on_command_error() is raised without a valid command."""
        embed = discord.Embed(title="Bakerbot: Command not found!", description="Try a different command, or see $help for command groups.", colour=utilities.errorColour)
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command()
    async def inject(self, ctx, cogname: str):
        """Injects an extension into Bakerbot. Requires owner permissions to execute."""
        self.bot.load_extension(cogname)

def setup(bot): bot.add_cog(debugger(bot))
