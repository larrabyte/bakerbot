import discord.ext.commands as commands
import titlecase as tcase
import discord
import urllib
import model
import ujson
import yarl

class Mangadex(commands.Cog):
    """A manga reader for Bakerbot!"""
    def __init__(self, bot: model.Bakerbot, backend: "MangadexBackend") -> None:
        self.colours = bot.utils.Colours
        self.icons = bot.utils.Icons
        self.embeds = bot.utils.Embeds
        self.backend = backend
        self.bot = bot

    @commands.group(invoke_without_subcommand=True)
    async def manga(self, ctx: commands.Context) -> None:
        """The parent command for the manga reader."""
        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                # There is no subcommand: inform the user about the module manager.
                summary = """Hi! Welcome to Bakerbot's manga reader.
                            This cog houses commands for searching and reading manga.
                            See `$help mangadex` for a full list of available subcommands."""

                embed = discord.Embed(colour=self.colours.regular, timestamp=self.embeds.now())
                embed.set_footer(text="Powered by the Mangadex API.", icon_url=self.icons.info)
                embed.description = summary
                await ctx.reply(embed=embed)
            else:
                # The subcommand was not valid: throw a fit.
                command = f"${ctx.command.name} {ctx.subcommand_passed}"
                summary = f"`{command}` is not a valid command."
                footer = "Try $help mangadex for a full list of available subcommands."
                embed = self.embeds.status(False, summary)
                embed.set_footer(text=footer, icon_url=self.icons.cross)
                await ctx.reply(embed=embed)

    @manga.command()
    async def info(self, ctx: commands.Context, *, title: str) -> None:
        """Get information on a manga given a `title` as the search query."""
        with ctx.typing():
            searches = await self.backend.search(title, 1)
            manga = searches["results"][0]
            thumbnail = await self.backend.cover(manga)
            manga = manga["data"]["attributes"]

        embed = discord.Embed(colour=self.colours.regular, timestamp=self.embeds.now())
        embed.set_footer(text="Powered by the Mangadex API.", icon_url=self.icons.info)
        embed.set_thumbnail(url=thumbnail)

        title = manga["title"]["en"] or "No title available."
        description = manga["description"]["en"][0:1024] or "No description available."
        embed.title = f"Mangadex: {title}"
        embed.description = description

        genres = [tag["attributes"]["name"]["en"] for tag in manga["tags"]]
        genreSubtitle = "Genres" if len(genres) > 1 else "Genre"
        embed.add_field(name=genreSubtitle, value=", ".join(genres))

        demo = manga["publicationDemographic"]
        demo = tcase.titlecase(demo)
        embed.add_field(name="Demographic", value=demo)
        await ctx.reply(embed=embed)

class MangadexBackend:
    """Backend Mangadex API wrapper."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.session = bot.session

    async def request(self, path: str) -> dict:
        """Sends a HTTP GET request to the Mangadex API."""
        url = yarl.URL(path, encoded=True)

        async with self.session.get(url) as resp:
            data = await resp.read()
            data = data.decode("utf-8")
            return ujson.loads(data)

    async def search(self, title: str, maximum: int) -> dict:
        """Search for some manga given a `title`."""
        params = {"title": title, "limit": maximum}
        encoder = urllib.parse.quote_plus
        params = urllib.parse.urlencode(params, quote_via=encoder)

        path = f"https://api.mangadex.org/manga?{params}"
        results = await self.request(path)
        return results

    async def cover(self, manga: dict) -> str:
        """Returns the filepath for a given cover's UUID."""
        mangaUUID = manga["data"]["id"]
        coverUUID = next(entry["id"] for entry in manga["relationships"] if entry["type"] == "cover_art")

        data = await self.request(f"https://api.mangadex.org/cover/{coverUUID}")
        filename = data["data"]["attributes"]["fileName"]
        return f"https://uploads.mangadex.org/covers/{mangaUUID}/{filename}"

def setup(bot: model.Bakerbot) -> None:
    backend = MangadexBackend(bot)
    cog = Mangadex(bot, backend)
    bot.add_cog(cog)
