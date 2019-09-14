"""Adds some functions for retarded speech."""
from discord.ext import tasks, commands
import random

@tasks.loop(seconds=1.0)
async def textloop(ctx, lines):
    if textloop.current_loop + 1 >= lines: textloop.stop()
    with open("./gentext.txt", "r") as text:
        text = text.readlines()
        num = random.randint(0, 11111)
        try: await ctx.send(text[num])
        except Exception: pass

class textgenerator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["text", "txt", "thonk"])
    async def textgen(self, ctx, linestoPrint: int=1):
        """Generates text by reading from a file."""
        await textloop.start(ctx, linestoPrint)

    @commands.command(aliases=["textstop"])
    async def stopgen(self, ctx):
        """Halts the `textloop`, if running."""
        textloop.stop()

def setup(bot): bot.add_cog(textgenerator(bot))