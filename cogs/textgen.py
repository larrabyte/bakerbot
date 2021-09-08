import backend.utilities as utilities
import backend.hugging as hugging
import model

import discord.ext.commands as commands
import typing as t
import discord

class Textgen(commands.Cog):
    def __init__(self, bot: model.Bakerbot, backend: hugging.Backend) -> None:
    """An interface to a text-generating neural network."""
        self.backend = backend
        self.maximum = 200
        self.bot = bot

    @commands.group(invoke_without_subcommand=True)
    async def text(self, ctx: commands.Context) -> None:
        """The parent command for the text generator."""
        summary = ("You've encountered Bakerbot's text generation command group! "
                   "See `$help textgen` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @text.command()
    async def generate(self, ctx: commands.Context, *, query: str) -> None:
        """Generates text with an optional `temperature` parameter."""
        async with ctx.typing():
            model = "EleutherAI/gpt-neo-2.7B"
            data = await self.backend.generate(model, query, self.maximum)

        data = discord.utils.escape_markdown(data)
        data = f"{data[0:1997]}..."
        await ctx.reply(data)

    @text.command()
    async def length(self, ctx: commands.Context, maximum: t.Optional[int]) -> None:
        """Queries or sets the maximum number of characters returned by the API."""
        info = f"The maximum is currently `{self.maximum}`." if maximum is None else f"The maximum has been set to `{maximum}`."
        embed = utilities.Embeds.standard(description=info)
        embed.set_footer(text="Powered by the Hugging Face API.", icon_url=utilities.Icons.info)
        self.maximum = maximum or self.maximum
        await ctx.reply(embed=embed)

def setup(bot: model.Bakerbot) -> None:
    backend = hugging.Backend(bot.secrets, bot.session)
    cog = Textgen(bot, backend)
    bot.add_cog(cog)
