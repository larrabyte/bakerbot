from operator import le
import utilities
import model

from discord.ext import commands
import discord
import asyncio
import random
import string
import io

class Random(commands.Cog):
    """Random ideas that I come up with every now and again."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    async def common_predefined_generator(self, ctx: commands.Context, available: str, length: int) -> str:
        """Common Unicode generation routine for when the available characters have already been precomputed."""
        generator = (random.choice(available) for i in range(length))

        if length <= utilities.Limits.MESSAGE_CHARACTERS:
            return "".join(c for c in generator)

        async with ctx.typing():
            return "".join(c for c in generator)

    async def common_random_generator(self, ctx: commands.Context, start: int, end: int, length: int) -> str:
        """Common Unicode generation routine for simple random character creation."""
        generator = (random.randint(start, end) for i in range(length))

        if length <= utilities.Limits.MESSAGE_CHARACTERS:
            return "".join(chr(c) for c in generator)

        async with ctx.typing():
            return "".join(chr(c) for c in generator)

    async def common_data_uploader(self, ctx: commands.Context, data: str) -> None:
        """Common uploading routine that handles file/message sending."""
        if len(data) <= utilities.Limits.MESSAGE_CHARACTERS:
            escaped = discord.utils.escape_markdown(data)
            if len(escaped) <= utilities.Limits.MESSAGE_CHARACTERS:
                return await ctx.reply(escaped)

        async with ctx.typing():
            encoded = data.encode("utf-8")
            rawdata = io.BytesIO(encoded)
            uploadable = discord.File(rawdata, "bytes.txt")
            await ctx.reply(file=uploadable)

    @commands.group()
    async def unicode(self, ctx: commands.Context) -> None:
        """The parent command for all things Unicode related."""
        summary = ("You've encountered Bakerbot's Unicode command group! "
                   "See `$help random` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @unicode.command()
    async def ascii(self, ctx: commands.Context, length: int=1) -> None:
        """Generates and returns random Unicode code points in the ASCII block."""
        text = await self.common_predefined_generator(ctx, string.ascii_letters, length)
        await self.common_data_uploader(ctx, text)

    @unicode.command()
    async def extendedascii(self, ctx: commands.Context, length: int=1) -> None:
        """Generates and returns random Unicode code points in the extended ASCII block."""
        text = await self.common_random_generator(ctx, 0x20, 0xFF, length)
        await self.common_data_uploader(ctx, text)

    @unicode.command()
    async def hangul(self, ctx: commands.Context, length: int=1) -> None:
        """Generates and returns random Unicode code points in the Hangul Jamo block."""
        text = await self.common_random_generator(ctx, 0x1100, 0x11FF, length)
        await self.common_data_uploader(ctx, text)

    @unicode.command()
    async def khmer(self, ctx: commands.Context, length: int=1) -> None:
        """Generates and returns random Unicode code points in the Khmer block."""
        text = await self.common_random_generator(ctx, 0x1780, 0x17FF, length)
        await self.common_data_uploader(ctx, text)

    @unicode.command()
    async def hiragana(self, ctx: commands.Context, length: int=1) -> None:
        """Generates and returns random Unicode code points in the Japanese hiragana block."""
        text = await self.common_random_generator(ctx, 0x3040, 0x309F, length)
        await self.common_data_uploader(ctx, text)

    @unicode.command()
    async def cjk(self, ctx: commands.Context, length: int=1) -> None:
        """Generates and returns random Unicode code points in the CJK block."""
        text = await self.common_random_generator(ctx, 0x4E00, 0x9FFF, length)
        await self.common_data_uploader(ctx, text)

    @commands.group()
    async def discord(self, ctx: commands.Context) -> None:
        """The parent command for Discord experiments."""
        summary = ("You've encountered Bakerbot's Discord experimentation lab! "
                   "See `$help random` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @discord.command()
    async def typing(self, ctx: commands.Context) -> None:
        """Starts typing in every available text channel."""
        coroutines = [channel.trigger_typing() for channel in ctx.guild.text_channels]
        await asyncio.gather(*coroutines)

def setup(bot: model.Bakerbot) -> None:
    cog = Random(bot)
    bot.add_cog(cog)
