import backends.hugging as hugging
import backends.neuro as neuro
import utilities
import model

import discord.ext.commands as commands
import typing as t
import discord
import io

class ModelFlags(commands.FlagConverter):
    """An object representing possible modifiable attributes in a `UserModel`."""
    backend: t.Optional[t.Literal["hugging", "neuro"]]
    identifier: t.Optional[str]
    remove_input: t.Optional[bool]
    temperature: t.Optional[float]
    maximum: t.Optional[int]

class Textgen(commands.Cog):
    """An interface to a text-generating neural network."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.mapping = {
            hugging.UserModel: hugging.Backend.generate,
            neuro.UserModel: neuro.Backend.generate,
            "hugging": hugging.UserModel,
            "neuro": neuro.UserModel
        }

        self.models = {}
        self.bot = bot

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        if ctx.author.id not in self.models:
            self.models[ctx.author.id] = neuro.UserModel()

    @commands.group(invoke_without_subcommand=True)
    async def text(self, ctx: commands.Context) -> None:
        """The parent command for the text generator."""
        summary = ("You've encountered Bakerbot's text generation command group! "
                   "See `$help textgen` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @text.command()
    async def generate(self, ctx: commands.Context, *, query: str) -> None:
        """Generates text with your personal model configuration."""
        model = self.models[ctx.author.id]
        generator = self.mapping[type(model)]

        async with ctx.typing():
            data = await generator(model, query)
            data = discord.utils.escape_markdown(data)

        if len(data) < utilities.Limits.MESSAGE_CHARACTERS:
            return await ctx.reply(data)

        # Chunk the message if it's over the limit.
        encoded = data.encode("utf-8")
        rawdata = io.BytesIO(encoded)
        uploadable = discord.File(rawdata, "generated.txt")
        await ctx.reply(file=uploadable)

    @text.command()
    async def configure(self, ctx: commands.Context, *, flags: ModelFlags) -> None:
        """Updates your personal model configuration."""
        if flags.backend is not None:
            self.models[ctx.author.id] = self.mapping[flags.backend]

        model = self.models[ctx.author.id]
        model.identifier = flags.identifier or model.identifier
        model.remove_input = flags.remove_input or model.remove_input
        model.temperature = flags.temperature or model.temperature
        model.maximum = flags.maximum or model.maximum

        binput = str(model.remove_input).lower()
        message = (f"Current (or updated?) model configuration:\n"
                   f" • Backend: {model.backend}\n"
                   f" • Identifier: {model.identifier}\n"
                   f" • Strip input from response? {binput}\n"
                   f" • Maximum no. of characters: {model.maximum}\n"
                   f" • Temperature: {model.temperature}")

        await ctx.reply(message)

def setup(bot: model.Bakerbot) -> None:
    cog = Textgen(bot)
    bot.add_cog(cog)
