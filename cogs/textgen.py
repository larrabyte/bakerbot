import utilities
import model

from discord.ext import commands
import concurrent.futures
import discord
import random
import io

def generate_chars(charset: tuple[int, int], count: int) -> str:
    """Character generation routine for execution in a process pool."""
    characters = "".join(chr(random.randint(charset[0], charset[1])) for i in range(count))
    return discord.utils.escape_markdown(characters)

class Textgen(commands.Cog):
    """Provides text-generation capabilities using various APIs."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.charsets = {
            # Mapping of character set names to a range of code points.
            "ascii": (0x41, 0x5A),
            "eascii": (0x20, 0xFF),
            "hangul": (0x1100, 0x11FF),
            "khmer": (0x1780, 0x17FF),
            "hiragana": (0x3040, 0x309F),
            "cjk": (0x4E00, 0x9FFF),
        }

        self.bot = bot

    @commands.command()
    async def unicode(self, ctx: commands.Context, charset: str | None, count: int=1) -> None:
        """Generate `count` random Unicode code points from `charset`."""
        if charset not in self.charsets:
            sets = " ".join(f"`{name}`" for name in self.charsets.keys())
            reply = f"None/invalid character set specified. Valid character sets are:\n • {sets}"
            return await ctx.reply(reply)

        with ctx.typing(), concurrent.futures.ProcessPoolExecutor() as pool:
            character_set = self.charsets[charset]
            result = await self.bot.loop.run_in_executor(pool, generate_chars, character_set, count)

            if len(result) > utilities.Limits.MESSAGE_CHARACTERS:
                encoded = result.encode("utf-8")
                data = io.BytesIO(encoded)
                uploadable = discord.File(data, "characters.txt")
                return await ctx.reply(file=uploadable)

            await ctx.reply(result)

    @commands.group(invoke_without_subcommand=True)
    async def text(self, ctx: commands.Context) -> None:
        """The parent command for the text generator."""
        summary = ("You've encountered Bakerbot's text generation command group! "
                   "See `$help textgen` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @text.command()
    async def generate(self, ctx: commands.Context, *, query: str) -> None:
        """Generate text with an initial query string."""
        pass

def setup(bot: model.Bakerbot) -> None:
    cog = Textgen(bot)
    bot.add_cog(cog)
