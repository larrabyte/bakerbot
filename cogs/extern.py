from discord.ext import commands
import subprocess
import utilities
import datetime
import asyncio
import discord

class extern(commands.Cog):
    """Implements an interface with external applications."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def quote(self, ctx: commands.Context):
        """Return a quote from `fortune`."""
        output = subprocess.run("bash -c fortune", encoding="utf-8", capture_output=True)
        await ctx.send(output.stdout)

    @commands.command()
    async def compile(self, ctx: commands.Context):
        """Compile some C/C++ code into an executable! Supports GCC for Windows and Linux."""
        if ctx.message.attachments:
            attached = ctx.message.attachments[0]
            await attached.save("data/code/main.cpp")
        else:
            embed = discord.Embed(title="Bakerbot: Compiler interface exception.", colour=utilities.errorColour, timestamp=datetime.datetime.utcnow())
            embed.description = "You must attach a file with source code to compile."
            embed.set_footer(text=f"Raised by {ctx.author.name} while trying to run ${ctx.command}.", icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title="Bakerbot: Compiler interface.", colour=utilities.regularColour)
        embed.add_field(name=":one: x86_64-pc-linux-gnu-g++", value="Creates native Linux binaries using WSL2.", inline=False)
        embed.add_field(name=":two: x86_64-w64-mingw32-g++", value="Creates native Windows binaries using WSL2.", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.name}.", icon_url=ctx.author.avatar_url)
        message = await ctx.send(embed=embed)

        reactEmojis = list(utilities.reactionOptions.keys())[:2]
        for emoji in reactEmojis: await message.add_reaction(emoji)
        launcher = "-Wall -Wextra -Wpedantic -static data/code/main.cpp -o data/code/a.out\""

        try:
            checklambda = lambda event, user: event.emoji in reactEmojis and user == ctx.author and event.message.id == message.id
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30, check=checklambda)
            if reaction.emoji == reactEmojis[0]: launcher = f"bash -c \"x86_64-pc-linux-gnu-g++ {launcher}"
            else: launcher = f"bash -c \"x86_64-w64-mingw32-g++ {launcher}"
        except asyncio.TimeoutError:
            await ctx.message.delete()
            await message.delete()
            return

        await message.delete()
        output = subprocess.run(launcher, encoding="utf-8", capture_output=True)
        if output.stderr: raise commands.CommandError(output.stderr)
        else: await ctx.send(file=discord.File("data/code/a.out"))

    @compile.error
    async def compileerror(self, ctx: commands.Command, error: object):
        """Error handler for the compile command."""
        if isinstance(error, commands.CommandError):
            embed = discord.Embed(title="Bakerbot: Compiler exception.", description=f"```{error.args[0]}```", colour=utilities.errorColour, timestamp=datetime.datetime.utcnow())
            embed.set_footer(text=f"Raised by g++ while trying to compile {ctx.author.name}'s code.", icon_url=utilities.crossMark)
            await ctx.send(embed=embed)
        else:
            debugger = self.bot.get_cog("debugger")
            await debugger.command_error_default(ctx, error)

def setup(bot): bot.add_cog(extern(bot))
