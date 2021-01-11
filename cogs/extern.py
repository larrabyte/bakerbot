from discord.ext import commands
import datetime as dt
import subprocess
import asyncio
import discord

class ExternError(commands.CommandError):
    NO_FILE_ATTACHED = 0
    COMPILER_ERROR   = 1
    ASYNCIO_TIMEOUT  = 2

    def __init__(self, exception_type: int, message: str=None) -> None:
        self.exception_type = exception_type
        self.message = message

    def __str__(self) -> str:
        if self.exception_type == self.NO_FILE_ATTACHED:
            return f"ExternError({self.exception_type}) raised: You must attach a file with source code to compile."
        elif self.exception_type == self.COMPILER_ERROR:
            return self.message
        elif self.exception_type == self.ASYNCIO_TIMEOUT:
            return f"ExternError({self.exception_type}) raised: Selection timed out."

class Extern(commands.Cog, name="extern"):
    """Implements an interface with external applications."""
    def __init__(self, bot: commands.Bot) -> None:
        bot.loop.create_task(self.startup())
        self.bot = bot

    async def startup(self) -> None:
        """Manages any cog prerequisites."""
        await self.bot.wait_until_ready()
        self.util = self.bot.get_cog("utilities")

    @commands.command()
    async def quote(self, ctx: commands.Context) -> None:
        """Return a quote from `fortune`."""
        output = subprocess.run("bash -c fortune", encoding="utf-8", capture_output=True)
        await ctx.send(output.stdout)

    @commands.command()
    async def compile(self, ctx: commands.Context) -> None:
        """Compile some C/C++ code into an executable! Supports GCC for Windows and Linux."""
        if not ctx.message.attachments: raise ExternError(ExternError.NO_FILE_ATTACHED)
        attached = ctx.message.attachments[0]
        await attached.save("data/code/main.cpp")

        embed = discord.Embed(title="Bakerbot: Compiler interface.",
                              colour=self.util.regular_colour,
                              timestamp=dt.datetime.utcnow())

        embed.add_field(name=":one: x86_64-pc-linux-gnu-g++", value="Creates native Linux binaries using WSL2.", inline=False)
        embed.add_field(name=":two: x86_64-w64-mingw32-g++", value="Creates native Windows binaries using WSL2.", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.name}.", icon_url=ctx.author.avatar_url)
        msg = await ctx.send(embed=embed)

        reactions = list(self.util.react_options.keys())[:2]
        for emoji in reactions: await msg.add_reaction(emoji)
        launcher = "-Wall -Wextra -Wpedantic -static data/code/main.cpp -o data/code/a.out\""
        check = lambda e, u: e.emoji in reactions and u == ctx.author and e.message.id == msg.id

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30, check=check)
            if reaction.emoji == reactions[0]: launcher = f"bash -c \"x86_64-pc-linux-gnu-g++ {launcher}"
            elif reaction.emoji == reactions[1]: launcher = f"bash -c \"x86_64-w64-mingw32-g++ {launcher}"
        except asyncio.TimeoutError:
            await msg.delete()
            raise ExternError(ExternError.ASYNCIO_TIMEOUT)

        await msg.delete()
        output = subprocess.run(launcher, encoding="utf-8", capture_output=True)
        if output.stderr: raise ExternError(ExternError.COMPILER_ERROR, f"```{output.stderr}```")
        else: await ctx.send(file=discord.File("data/code/a.out"))

def setup(bot): bot.add_cog(Extern(bot))
