from backends import hugging
from backends import openai
from backends import neuro
from abcs import text
import utilities
import model

from discord.ext import commands
import typing as t
import discord
import random
import string
import io

class ModelFlags(commands.FlagConverter):
    """An object representing possible modifiable attributes in a `Model`."""
    backend: t.Optional[str]
    identifier: t.Optional[str]
    remove_input: t.Optional[bool]
    temperature: t.Optional[float]
    maximum: t.Optional[int]
    repetition_penalty: t.Optional[float]

class Textgen(commands.Cog):
    """An interface to the Hugging Face and Neuro text-generating APIs."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.apis = {
            "hugging": hugging.Backend,
            "neuro": neuro.Backend,
            "openai": openai.Backend
        }

        self.models = {}
        self.bot = bot

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        """Ensures that a user has a model configuration in the dictionary."""
        if ctx.author.id not in self.models:
            # text.Model(neuro.Backend, "60ca2a1e54f6ecb69867c72c")
            model = text.Model(openai.Backend, "davinci")
            self.models[ctx.author.id] = model

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

    @commands.group(invoke_without_subcommand=True)
    async def text(self, ctx: commands.Context) -> None:
        """The parent command for the text generator."""
        summary = ("You've encountered Bakerbot's text generation command group! "
                   "See `$help textgen` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @text.command()
    async def generate(self, ctx: commands.Context, *, query: str) -> None:
        """Generates text with your personal model configuration."""
        async with ctx.typing():
            model = self.models[ctx.author.id]
            data = await model.generate(query)

        data = discord.utils.escape_markdown(data)
        if len(data) <= utilities.Limits.MESSAGE_CHARACTERS:
            return await ctx.reply(data)

        # Upload the message as a file if it's over the limit.
        encoded = data.encode("utf-8")
        rawdata = io.BytesIO(encoded)
        uploadable = discord.File(rawdata, "generated.txt")
        await ctx.reply(file=uploadable)

    @text.command()
    async def configure(self, ctx: commands.Context, *, flags: ModelFlags) -> None:
        """Updates your personal model configuration."""
        model = self.models[ctx.author.id]

        if flags.backend is not None:
            if flags.backend.lower() in self.apis:
                model.backend = self.apis[flags.backend.lower()]
            else:
                options = ", ".join(self.apis.keys())
                fail = f"Invalid backend. Options include: {options}."
                return await ctx.reply(fail)

        model.identifier = flags.identifier or model.identifier
        model.remove_input = flags.remove_input or model.remove_input
        model.temperature = flags.temperature or model.temperature
        model.maximum = flags.maximum or model.maximum
        model.repetition_penalty = flags.repetition_penalty or model.repetition_penalty

        modified = all(v is not None for k, v in flags)
        view = ConfigureView() if not modified else None
        verb = "Updated" if modified else "Current"

        text = (f"{verb} model configuration:\n"
                f" • API backend/identifier: {model.backend.name()} | {model.identifier}\n"
                f" • Input stripping/character max: {str(model.remove_input).lower()} | {model.maximum}\n"
                f" • Repetition penalty/temperature: {model.repetition_penalty} | {model.temperature}")

        await ctx.reply(text, view=view)

class ConfigureView(utilities.View):
    """A subclass of `utilities.View` for displaying model configuration instructions."""
    @discord.ui.button(label="Click here to learn how to configure your model!")
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Handles model configuration help requests."""
        tutorial = ("To modify your model, pass arguments like so:\n"
                    "`$text configure temperature: 1.0 maximum: 9000`\n\n"
                    "All arguments are optional. Here is the full list of parameters:\n"
                    " • **backend** specifies the API to use.\n"
                    " • **identifier** specifies the model and is specific to each API.\n"
                    " • **remove_input** specifies whether the original input is included.\n"
                    " • **temperature** specifies the model's temperature.\n"
                    " • **maximum** specifies the maximum number of characters.\n"
                    " • **repetition_penalty** specifies the repetition penalty.")

        await interaction.response.send_message(tutorial, ephemeral=True)

def setup(bot: model.Bakerbot) -> None:
    cog = Textgen(bot)
    bot.add_cog(cog)
