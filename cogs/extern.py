from discord.ext import commands
import subprocess
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
    async def compile(self, ctx: commands.Context, os: str, *, code: str):
        """Compile some C code into an executable! Supports GCC for Windows and Linux."""
        with open("data/code/main.c", "w") as f:
            f.write(code.replace("```", ""))

        subprocstr = "-Wall -Wextra -Wpedantic -static data/code/main.c -o data/code/a.out\""
        if os == "linux" or os == "gnu": subprocstr = "bash -c \"x86_64-pc-linux-gnu-gcc " + subprocstr
        elif os == "windows" or os == "win": subprocstr = "bash -c \"x86_64-w64-mingw32-gcc " + subprocstr
        else: return await ctx.send("Unsupported operating system. Currently, only Windows and Linux are supported.")

        output = subprocess.run(subprocstr, encoding="utf-8", capture_output=True)
        if output.stderr: await ctx.send(output.stderr)
        else: await ctx.send(file=discord.File("data/code/a.out"))

def setup(bot): bot.add_cog(extern(bot))
