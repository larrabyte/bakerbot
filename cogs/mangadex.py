import backends.mangadex as mangadex
import utilities
import model

import discord.ext.commands as commands
import titlecase as tcase
import typing as t
import discord

class Mangadex(commands.Cog):
    """Bakerbot's implementation of the Mangadex API (v5)."""
    def __init__(self, bot: model.Bakerbot, backend: mangadex.Backend) -> None:
        self.backend = backend
        self.bot = bot

    @commands.group(invoke_without_subcommand=True)
    async def manga(self, ctx: commands.Context) -> None:
        """The parent command for the manga reader."""
        summary = ("You've encountered the Mangadex command group!"
                    "See `$help mangadex` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @manga.command()
    async def info(self, ctx: commands.Context, *, title: str) -> None:
        """Returns informatioan about a specific manga."""
        async with ctx.typing():
            searches = await self.backend.search(title, 1)
            data = searches["results"][0]
            mangaUUID = self.backend.mangaUUID(data)
            coverUUID = self.backend.coverUUID(data)
            thumbnail = await self.backend.cover(mangaUUID, coverUUID)

        embed = utilities.Embeds.standard()
        embed.set_footer(text="Powered by the Mangadex API.", icon_url=utilities.Icons.INFO)
        embed.set_thumbnail(url=thumbnail)

        manga = data["data"]["attributes"]
        title = manga["title"]["en"] or "No title available."
        description = manga["description"]["en"][0:1024] or "No description available."
        embed.title = f"Mangadex: {title}"
        embed.description = description

        genres = [tag["attributes"]["name"]["en"] for tag in manga["tags"]]
        genre_subtitle = "Genres" if len(genres) > 1 else "Genre"
        embed.add_field(name=genre_subtitle, value=", ".join(genres))

        demo = manga["publicationDemographic"]
        demo = tcase.titlecase(demo) if demo is not None else "Unknown demographic."
        embed.add_field(name="Demographic", value=demo)
        await ctx.reply(embed=embed)

    @manga.command()
    async def read(self, ctx: commands.Context, *, title: str) -> None:
        """Initialises an instance of Bakerbot's manga reader."""
        async with ctx.typing():
            searches = await self.backend.search(title, 1)
            data = searches["results"][0]
            uuid = self.backend.mangaUUID(data)
            aggregate = await self.backend.aggregate(uuid)

        volumes = aggregate["volumes"].values()
        num_chapters = sum(volume["count"] for volume in volumes)
        chapters = []
        offset = 0

        while num_chapters > 0:
            limit = min(num_chapters, 500)
            data = await self.backend.feed(uuid, limit, offset)
            chapters += data["results"]
            num_chapters -= limit
            offset += 500

        paginator = utilities.Paginator()
        paginator.placeholder = "Chapters"

        for index, chapter in enumerate(chapters):
            volume_index = chapter["data"]["attributes"]["volume"]
            chapter_index = chapter["data"]["attributes"]["chapter"]
            description = f"Volume {volume_index}, " if volume_index is not None else ""
            description += f"Chapter {chapter_index}"
            title = chapter["data"]["attributes"]["title"] or description

            title = utilities.Limits.limit(title, utilities.Limits.SELECT_LABEL)
            description = utilities.Limits.limit(description, utilities.Limits.SELECT_DESCRIPTION)
            option = discord.SelectOption(label=title, value=str(index), description=description)
            paginator.add(option)

        message = await ctx.reply("Select any chapter to start reading.", view=paginator)

        if (selection := await paginator.wait()) is not None:
            chapter = chapters[int(selection)]
            identifier = chapter["data"]["id"]
            digest = chapter["data"]["attributes"]["hash"]
            images = chapter["data"]["attributes"]["data"]
            reader = await MangaReader.create(self, identifier, digest, images)
            await reader.run(message)

class MangaReader(utilities.View):
    """A subclass of `utilities.View` built for image iteration."""
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

def setup(bot: model.Bakerbot) -> None:
    backend = mangadex.Backend(bot.session)
    cog = Mangadex(bot, backend)
    bot.add_cog(cog)
