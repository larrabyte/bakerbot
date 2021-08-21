import discord.ext.commands as commands
import libs.utilities as utilities
import titlecase as tcase
import typing as t
import discord
import urllib
import model
import ujson
import yarl

class Mangadex(commands.Cog):
    """A manga reader for Bakerbot!"""
    def __init__(self, bot: model.Bakerbot, backend: "MangadexBackend") -> None:
        self.backend = backend
        self.bot = bot

    @commands.group(invoke_without_subcommand=True)
    async def manga(self, ctx: commands.Context) -> None:
        """The parent command for the manga reader."""
        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                # There is no subcommand: inform the user about the manga reader.
                summary = """Hi! Welcome to Bakerbot's manga reader.
                            This cog houses commands for searching and reading manga.
                            See `$help mangadex` for a full list of available subcommands."""

                embed = utilities.Embeds.standard()
                embed.set_footer(text="Powered by the Mangadex API.", icon_url=utilities.Icons.info)
                embed.description = summary
                await ctx.reply(embed=embed)
            else:
                # The subcommand was not valid: throw a fit.
                command = f"${ctx.command.name} {ctx.subcommand_passed}"
                summary = f"`{command}` is not a valid command."
                footer = "Try $help mangadex for a full list of available subcommands."
                embed = utilities.Embeds.status(False, summary)
                embed.set_footer(text=footer, icon_url=utilities.Icons.cross)
                await ctx.reply(embed=embed)

    @manga.command()
    async def info(self, ctx: commands.Context, *, title: str) -> None:
        """Get information on a manga given a `title` as the search query."""
        async with ctx.typing():
            searches = await self.backend.search(title, 1)
            data = searches["results"][0]
            mangaUUID = self.backend.mangaUUID(data)
            coverUUID = self.backend.coverUUID(data)
            thumbnail = await self.backend.cover(mangaUUID, coverUUID)

        embed = utilities.Embeds.standard()
        embed.set_footer(text="Powered by the Mangadex API.", icon_url=utilities.Icons.info)
        embed.set_thumbnail(url=thumbnail)

        manga = data["data"]["attributes"]
        title = manga["title"]["en"] or "No title available."
        description = manga["description"]["en"][0:1024] or "No description available."
        embed.title = f"Mangadex: {title}"
        embed.description = description

        genres = [tag["attributes"]["name"]["en"] for tag in manga["tags"]]
        genreSubtitle = "Genres" if len(genres) > 1 else "Genre"
        embed.add_field(name=genreSubtitle, value=", ".join(genres))

        demo = manga["publicationDemographic"]
        demo = tcase.titlecase(demo) if demo is not None else "Unknown demographic."
        embed.add_field(name="Demographic", value=demo)
        await ctx.reply(embed=embed)

    @manga.command()
    async def read(self, ctx: commands.Context, *, title: str) -> None:
        """Read a manga (using `title` as the search query)."""
        async with ctx.typing():
            searches = await self.backend.search(title, 1)
            data = searches["results"][0]
            uuid = self.backend.mangaUUID(data)
            aggregate = await self.backend.aggregate(uuid)

        volumes = aggregate["volumes"].values()
        numChapters = sum(volume["count"] for volume in volumes)
        chapters = []
        offset = 0

        while numChapters > 0:
            limit = min(numChapters, 500)
            data = await self.backend.feed(uuid, limit, offset)
            chapters += data["results"]
            numChapters -= limit
            offset += 500

        paginator = utilities.Paginator()
        paginator.placeholder = "Chapters"

        for index, chapter in enumerate(chapters):
            volumeIndex = chapter["data"]["attributes"]["volume"]
            chapterIndex = chapter["data"]["attributes"]["chapter"]
            description = f"Volume {volumeIndex}, " if volumeIndex is not None else ""
            description += f"Chapter {chapterIndex}"

            title = chapter["data"]["attributes"]["title"] or description
            label = f"{title[0:22]}..." if len(title) > 25 else title

            option = discord.SelectOption(label=label, value=str(index), description=description)
            paginator.add(option)

        message = await ctx.reply("Select any chapter to start reading.", view=paginator)

        if (selection := await paginator.wait()) is not None:
            chapter = chapters[int(selection)]
            identifier = chapter["data"]["id"]
            digest = chapter["data"]["attributes"]["hash"]
            images = chapter["data"]["attributes"]["data"]
            reader = await MangaReader.create(self, identifier, digest, images)
            await reader.run(message)

class MangaReader(discord.ui.View):
    """A subclass of `discord.ui.View` built for image iteration."""
    @classmethod
    async def create(self, cog: Mangadex, identifier: str, digest: str, images: t.List[str]) -> "MangaReader":
        instance = MangaReader()
        instance.backend = cog.backend
        instance.identifier = identifier
        instance.images = images
        instance.digest = digest
        instance.cursor = 0

        instance.base = await cog.backend.server(identifier)
        return instance

    def current(self) -> str:
        """Returns the current image URL."""
        return f"{self.base}/data/{self.digest}/{self.images[self.cursor]}"

    async def run(self, message: discord.Message) -> None:
        """Starts the manga reader."""
        await message.edit(content=self.current(), view=self)

    @discord.ui.button(label="First")
    async def first(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Moves the manga reader to the first page."""
        self.cursor = 0
        await interaction.response.edit_message(content=self.current())

    @discord.ui.button(label="Previous")
    async def prev(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Moves the manga reader to the previous page."""
        if self.cursor < 1:
            return await interaction.response.defer()

        self.cursor -= 1
        await interaction.response.edit_message(content=self.current())

    @discord.ui.button(label="Next")
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Moves the manga reader to the next page."""
        if self.cursor >= len(self.images) - 1:
            return await interaction.response.defer()

        self.cursor += 1
        await interaction.response.edit_message(content=self.current())

    @discord.ui.button(label="Last")
    async def last(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Moves the manga reader to the last page."""
        self.cursor = len(self.images) - 1
        await interaction.response.edit_message(content=self.current())

class MangadexBackend:
    """Backend Mangadex API wrapper."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.session = bot.session

    def mangaUUID(self, manga: dict) -> str:
        """Returns the manga UUID from a given manga object."""
        return manga["data"]["id"]

    def coverUUID(self, manga: dict) -> str:
        """Returns the cover UUID from a given manga object."""
        return next(entry["id"] for entry in manga["relationships"] if entry["type"] == "cover_art")

    async def request(self, path: str) -> dict:
        """Sends a HTTP GET request to the Mangadex API."""
        url = yarl.URL(path, encoded=True)

        async with self.session.get(url) as resp:
            data = await resp.read()
            data = data.decode("utf-8")
            return ujson.loads(data)

    async def cover(self, manga: str, cover: str) -> str:
        """Returns the URL for a cover given manga and cover UUIDs."""
        data = await self.request(f"https://api.mangadex.org/cover/{cover}")
        filename = data["data"]["attributes"]["fileName"]
        return f"https://uploads.mangadex.org/covers/{manga}/{filename}"

    async def server(self, uuid: str) -> str:
        """Returns a valid MD@H server for a given manga UUID."""
        path = f"https://api.mangadex.org/at-home/server/{uuid}"
        results = await self.request(path)
        return results["baseUrl"]

    async def search(self, title: str, maximum: int) -> dict:
        """Search for some manga given a `title`."""
        params = {"title": title, "limit": maximum}
        encoder = urllib.parse.quote_plus
        params = urllib.parse.urlencode(params, quote_via=encoder)

        path = f"https://api.mangadex.org/manga?{params}"
        results = await self.request(path)
        return results

    async def aggregate(self, uuid: str) -> dict:
        """Returns an aggregate of volumes/chapters for a manga using a given UUID."""
        path = f"https://api.mangadex.org/manga/{uuid}/aggregate?translatedLanguage[]=en"
        results = await self.request(path)
        return results

    async def feed(self, uuid: str, limit: int, offset: int) -> dict:
        """Returns the feed of a manga given a UUID, limit and offset."""
        path = f"https://api.mangadex.org/manga/{uuid}/feed?limit={limit}&offset={offset}&translatedLanguage[]=en&order[chapter]=asc"
        results = await self.request(path)
        return results

def setup(bot: model.Bakerbot) -> None:
    backend = MangadexBackend(bot)
    cog = Mangadex(bot, backend)
    bot.add_cog(cog)
