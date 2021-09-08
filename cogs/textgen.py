import backend.utilities as utilities
import backend.hugging as hugging
import backend.neuro as neuro
import model

import discord.ext.commands as commands
import typing as t
import discord
import io

class Textgen(commands.Cog):
    """An interface to a text-generating neural network."""
    def __init__(self, bot: model.Bakerbot, backend: neuro.Backend) -> None:
        self.backend = backend
        self.model = neuro.Model("60ca2a1e54f6ecb69867c72c")
        self.bot = bot

    @commands.group(invoke_without_subcommand=True)
    async def text(self, ctx: commands.Context) -> None:
        """The parent command for the text generator."""
        summary = ("You've encountered Bakerbot's text generation command group! "
                   "See `$help textgen` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @text.command()
    async def generate(self, ctx: commands.Context, temperature: t.Optional[float]=1.0, *, query: str) -> None:
        """Generates text with an optional `temperature` parameter."""
        async with ctx.typing():
            data = await self.backend.generate(self.model, query)
            data = discord.utils.escape_markdown(data)

        if len(data) < utilities.Limits.message_content:
            return await ctx.reply(data)

        # Chunk the message if it's over the limit.
        encoded = data.encode("utf-8")
        rawdata = io.BytesIO(encoded)
        uploadable = discord.File(rawdata, "generated.txt")
        await ctx.reply(file=uploadable)

    @text.command()
    async def length(self, ctx: commands.Context, maximum: t.Optional[int]) -> None:
        """Queries or sets the maximum number of characters returned by the API."""
        self.model.maximum = maximum or self.model.maximum
        await ctx.reply(f"The current maximum is (now?) `{self.model.maximum}` tokens.")

def setup(bot: model.Bakerbot) -> None:
    backend = neuro.Backend(bot.secrets, bot.session)
    cog = Textgen(bot, backend)
    bot.add_cog(cog)
