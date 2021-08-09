import discord.ext.commands as commands
import typing as t
import discord
import model
import ujson
import yarl

class Textgen(commands.Cog):
    """Want to generate some text? Try the text generator!"""
    def __init__(self, bot: model.Bakerbot, backend: "TextgenBackend") -> None:
        self.colours = bot.utils.Colours
        self.icons = bot.utils.Icons
        self.embeds = bot.utils.Embeds
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

                embed = discord.Embed(colour=self.colours.regular, timestamp=discord.utils.utcnow())
                embed.description = summary
                embed.set_footer(text="Powered by the Hugging Face API.", icon_url=self.icons.info)
                await ctx.reply(embed=embed)
            else:
                # The subcommand was not valid: throw a fit.
                command = f"${ctx.command.name} {ctx.subcommand_passed}"
                summary = f"`{command}` is not a valid command."
                footer = "Try $help textgen for a full list of available subcommands."
                embed = self.embeds.status(False, summary)
                embed.set_footer(text=footer, icon_url=self.icons.cross)
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
        embed = discord.Embed(description=info, colour=self.colours.regular, timestamp=discord.utils.utcnow())
        embed.set_footer(text="Powered by the Hugging Face API.", icon_url=self.icons.info)
        self.maximum = maximum or self.maximum
        await ctx.reply(embed=embed)

class TextgenBackend:
    """A backend Hugging Face API wrapper."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.key = bot.secrets.get("hugging-token", None)
        self.base = "https://api-inference.huggingface.co"
        self.session = bot.session

    async def request(self, path: str, payload: dict, headers: dict) -> object:
        """Send a HTTP POST request to the Hugging Face Inference API."""
        url = yarl.URL(f"{self.base}/{path}", encoded=True)

        async with self.session.post(url, json=payload, headers=headers) as resp:
            data = await resp.read()
            data = data.decode("utf-8")
            data = ujson.loads(data)
            return data

    async def generate(self, model: str, query: str, chars: int) -> str:
        """Generates text from a given `model` and `query` string."""
        if self.key is None:
            raise RuntimeError("Request attempted without API key.")

        headers = {"Authorization": f"Bearer {self.key}"}
        payload = {"inputs": query, "options": {"wait_for_model": True}, "parameters": {"max_length": chars}}
        data = await self.request(f"models/{model}", payload, headers)

        if isinstance(data, list):
            return data[0]["generated_text"]

        return data["error"]

def setup(bot: model.Bakerbot) -> None:
    backend = TextgenBackend(bot)
    cog = Textgen(bot, backend)
    bot.add_cog(cog)
