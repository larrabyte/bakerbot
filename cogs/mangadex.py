from backends import mangadex
import utilities
import model

from discord.ext import commands
import titlecase
import discord
import typing

class Mangadex(commands.Cog):
    """Bakerbot's implementation of the Mangadex API (v5)."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    def optional_titlecase(self, string: str | None, default: str) -> str:
        """Optionally apply a titlecase transformation on `string`, else return the default."""
        if string is not None:
            return titlecase.titlecase(string)

        return default

    @commands.group(invoke_without_subcommand=True)
    async def manga(self, ctx: commands.Context) -> None:
        """The parent command for the manga reader."""
        summary = ("You've encountered the Mangadex command group! "
                   "See `$help mangadex` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @manga.command()
    async def info(self, ctx: commands.Context, *, title: str) -> None:
        """Return information about a specific manga."""
        async with ctx.typing():
            manga = await mangadex.Backend.manga(title)
            author = await manga.author()
            cover = await manga.cover()

        embed = utilities.Embeds.standard()
        embed.title = f"Mangadex: {manga.title}"
        embed.url = f"{mangadex.Backend.client}/title/{manga.identifier}"
        embed.set_footer(text="Powered by the Mangadex API.", icon_url=utilities.Icons.INFO)

        embed.description = "No description available."
        if manga.description is not None:
            stripped = manga.description.strip()
            embed.description = utilities.Limits.limit(stripped, 256)

        if cover is not None:
            embed.set_thumbnail(url=cover)

        embed.add_field(name="🗿  Author", value=author)
        genres = ", ".join(tag.name for tag in manga.tags) or "No genres available."
        tgenre = "📖  Genres" if len(manga.tags) > 1 else "📖  Genre"
        embed.add_field(name=tgenre, value=genres)

        demographic = self.optional_titlecase(manga.demographic, "Unknown demographic.")
        status = self.optional_titlecase(manga.status, "Unknown status.")
        rating = titlecase.titlecase(manga.content_rating)
        last_chapter = self.optional_titlecase(manga.last_chapter, "Not available.")
        embed.add_field(name="🤺  Demographic", value=demographic)
        embed.add_field(name="✍🏼  Status", value=status)
        embed.add_field(name="👹  Content Rating", value=rating)
        embed.add_field(name="🏗️  New Chapter(s)", value=last_chapter)
        await ctx.reply(embed=embed)

    @manga.command()
    async def read(self, ctx: commands.Context, *, title: str) -> None:
        """Initialise an instance of Bakerbot's manga reader."""
        async with ctx.typing():
            manga = await mangadex.Backend.manga(title)
            await manga.aggregate(language="en")
            await manga.feed(language="en")

        paginator = utilities.Paginator()
        paginator.placeholder = "Manga chapters: Options"
        available = []

        for index, chapter in enumerate(manga.chapters):
            if chapter.volume is not None:
                available.append(f"Volume {chapter.volume}")
            if chapter.chapter is not None:
                available.append(f"Chapter {chapter.chapter}")

            description = ", ".join(available) or "No chapter/volume number available."
            label = utilities.Limits.limit(chapter.title or description, utilities.Limits.SELECT_LABEL)
            value = utilities.Limits.limit(description, utilities.Limits.SELECT_DESCRIPTION)
            option = discord.SelectOption(label=label, value=str(index), description=value)
            paginator.add(option)
            available.clear()

        message = await ctx.reply("Select a chapter to start reading.", view=paginator)
        if (choice := await paginator.wait()) is not None:
            reader = MangaReaderView(manga, int(choice))
            await reader.run(message)

class MangaReaderView(utilities.View):
    """A manga reader view that can be used to navigate through a manga's chapters."""
    def __init__(self, manga: mangadex.Manga, index: int, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        self.manga = manga
        self.current_chapter = index
        self.chapter_index = 0

    async def get_current_page(self) -> str:
        """Return the current image pointed to by the chapter and index cursors."""
        chapter = self.manga.chapters[self.current_chapter]
        page = chapter.data_saver[self.chapter_index]

        if chapter.base_url is None:
            await chapter.base()

        # Use data saver so clients don't spend so much time downloading image data.
        return f"{chapter.base_url}/data-saver/{chapter.hash}/{page}"

    async def run(self, message: discord.Message) -> None:
        """Start the manga reader using `message` as the output."""
        link = await self.get_current_page()
        await message.edit(content=link, view=self)

    @discord.ui.button(label="First")
    async def first(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Handle interactions to return to the first page."""
        if self.chapter_index < 1:
            error = "You're already at the first page!"
            return await interaction.response.send_message(content=error, ephemeral=True)

        self.chapter_index = 0
        link = await self.get_current_page()
        await interaction.response.edit_message(content=link)

    @discord.ui.button(label="Previous")
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Handle requests to move back one page."""
        if self.chapter_index < 1:
            error = "You're already at the first page!"
            return await interaction.response.send_message(content=error, ephemeral=True)

        self.chapter_index -= 1
        link = await self.get_current_page()
        await interaction.response.edit_message(content=link)

    @discord.ui.button(label="Next")
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Handle requests to move forward one page."""
        chapter = self.manga.chapters[self.current_chapter]
        if self.chapter_index >= len(chapter.data) - 1:
            error = "You're already at the last page!"
            return await interaction.response.send_message(content=error, ephemeral=True)

        self.chapter_index += 1
        link = await self.get_current_page()
        await interaction.response.edit_message(content=link)

    @discord.ui.button(label="Last")
    async def last(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Handle requests to move forward to the last page."""
        chapter = self.manga.chapters[self.current_chapter]
        if self.chapter_index >= len(chapter.data) - 1:
            error = "You're already at the last page!"
            return await interaction.response.send_message(content=error, ephemeral=True)

        self.chapter_index = len(chapter.data) - 1
        link = await self.get_current_page()
        await interaction.response.edit_message(content=link)

    @discord.ui.button(label="Previous Chapter", row=2)
    async def last_chapter(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Handle requests to move back a whole chapter."""
        if self.current_chapter < 1:
            error = "You're already at the first chapter!"
            return await interaction.response.send_message(content=error, ephemeral=True)

        self.current_chapter -= 1
        self.chapter_index = 0
        link = await self.get_current_page()
        await interaction.response.edit_message(content=link)

    @discord.ui.button(label="Next Chapter", row=2)
    async def next_chapter(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Handle requests to move to the next chapter."""
        if self.current_chapter >= len(self.manga.chapters) - 1:
            error = "You're already at the last chapter!"
            return await interaction.response.send_message(content=error, ephemeral=True)

        self.current_chapter = len(self.manga.chapters) - 1
        self.chapter_index = 0
        link = await self.get_current_page()
        await interaction.response.edit_message(content=link)

def setup(bot: model.Bakerbot) -> None:
    cog = Mangadex(bot)
    bot.add_cog(cog)
