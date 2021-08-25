import backend.utilities as utilities
import backend.hugging as hugging
import model

import discord.ext.commands as commands
import typing as t
import discord

class Textgen(commands.Cog):
    """Want to generate some text? Try the text generator!"""
    def __init__(self, bot: model.Bakerbot, backend: hugging.Backend) -> None:
        self.backend = backend
        self.maximum = 200
        self.bot = bot

    @commands.group(invoke_without_subcommand=True)
    async def text(self, ctx: commands.Context) -> None:
        """The parent command for the text generation API."""
        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                # There is no subcommand: inform the user about the text generator.
                summary = """Hi! Welcome to Bakerbot's text generation command group.
                            This cog houses commands that interface with the Hugging Face API.
                            See `$help textgen` for a full list of available subcommands."""

                embed = utilities.Embeds.standard()
                embed.description = summary
                embed.set_footer(text="Powered by the Hugging Face API.", icon_url=utilities.Icons.info)
                await ctx.reply(embed=embed)
            else:
                # The subcommand was not valid: throw a fit.
                command = f"${ctx.command.name} {ctx.subcommand_passed}"
                summary = f"`{command}` is not a valid command."
                footer = "Try $help textgen for a full list of available subcommands."
                embed = utilities.Embeds.status(False, summary)
                embed.set_footer(text=footer, icon_url=utilities.Icons.cross)
                await ctx.reply(embed=embed)

    @text.command()
    async def generate(self, ctx: commands.Context, *, query: str) -> None:
        """Generates text, using `query` as the base."""
        async with ctx.typing():
            model = "EleutherAI/gpt-neo-2.7B"
            data = await self.backend.generate(model, query, self.maximum)

        data = discord.utils.escape_markdown(data)
        data = f"{data[0:1997]}..."
        await ctx.reply(data)

    @text.command()
    async def maxlen(self, ctx: commands.Context, maximum: t.Optional[int]) -> None:
        """Query or set the maximum number of characters returned by the API."""
        info = f"The maximum is currently `{self.maximum}`." if maximum is None else f"The maximum has been set to `{maximum}`."
        embed = utilities.Embeds.standard(description=info)
        embed.set_footer(text="Powered by the Hugging Face API.", icon_url=utilities.Icons.info)
        self.maximum = maximum or self.maximum
        await ctx.reply(embed=embed)

def setup(bot: model.Bakerbot) -> None:
    backend = hugging.Backend(bot.secrets, bot.session)
    cog = Textgen(bot, backend)
    bot.add_cog(cog)
