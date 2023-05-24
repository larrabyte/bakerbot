import discord.app_commands as application
import discord.ext.commands as commands
import manga.backend as backend

import aiohttp
import discord
import limits
import views
import re

class Manga(commands.GroupCog):
    def __init__(self, bot: commands.Bot, session: aiohttp.ClientSession):
        super().__init__()
        self.session = session
        self.bot = bot

    @application.command(description="Get information about a manga via Mangadex.")
    @application.describe(title="The title of a manga.")
    async def info(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer(thinking=True)
        if not (titles := await backend.search(self.session, title)):
            return await interaction.followup.send("No manga found.")

        paginator = views.Paginator(
            lambda title: (
                limits.limit(title.title or "Unknown Title", limits.SELECT_LABEL),
                limits.limit(title.description or "No description given.", limits.SELECT_DESCRIPTION)
            ),

            titles
        )

        await interaction.followup.send(view=paginator, suppress_embeds=True)

        if (manga := await paginator.wait()) is not None:
            authors = await manga.authors(self.session)
            authors = ", ".join(authors)
            tags = ", ".join(manga.tags)
            summary = manga.description or "No description given."
            summary = re.sub("\\s{2,}", " ", summary)
            summary = limits.limit(summary, 512)

            message = (
                f"# {manga.title or 'Unknown Title'}\n"
                f"- Author: {authors or 'Unknown'}\n"
                f"- Tags: {tags or 'Unknown'}\n"
                f"- Demographic: {manga.demographic or 'Unknown'}\n"
                f"- Status: {manga.status or 'Unknown'}\n"
                f"- Year of Release: {manga.year or 'Unknown'}\n"
                f"{summary}"
            )

            await interaction.edit_original_response(content=message, view=None)

    @application.command(description="Read a manga via Mangadex.")
    @application.describe(title="The title of a manga.")
    async def read(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer(thinking=True)
        if not (titles := await backend.search(self.session, title)):
            return await interaction.followup.send("No manga found.")

        chapters = await titles[0].chapters(self.session)
        paginator = views.Paginator(
            lambda chapter: (
                (f"Volume {vol}, " if (vol := chapter.volume) is not None else "") + f"Chapter {chapter.chapter}",
                ""
            ),

            chapters
        )

        await interaction.followup.send(view=paginator)

        if (chapter := await paginator.wait()) is not None:
            pages = await chapter.pages(self.session)
            reader = Reader(self.session, chapters, chapter, pages)
            await interaction.edit_original_response(content=pages[0], view=reader)

class Reader(views.View):
    """An interactive manga reader built with Discord components."""
    def __init__(self, session: aiohttp.ClientSession, chapters: list[backend.Chapter], chapter: backend.Chapter, pages: list[str]):
        super().__init__()
        self.session = session

        # Remember that the chapters are ordered backwards.
        self.chapters = chapters
        self.pages = pages

        self.chapter = chapters.index(chapter)
        self.page = 0

    @discord.ui.button(label="Last", row=0)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Move the reader to the last page."""
        self.page = len(self.pages) - 1
        await interaction.response.edit_message(content=self.pages[self.page])

    @discord.ui.button(label="Next", row=0)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Move the reader to the next page."""
        self.page = min(len(self.pages) - 1, self.page + 1)
        await interaction.response.edit_message(content=self.pages[self.page])

    @discord.ui.button(label="Previous", row=0)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Move the reader to the previous page."""
        self.page = max(0, self.page - 1)
        await interaction.response.edit_message(content=self.pages[self.page])

    @discord.ui.button(label="First", row=0)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Move the reader to the first page."""
        self.page = 0
        await interaction.response.edit_message(content=self.pages[self.page])

    @discord.ui.button(label="Next Chapter", row=1)
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Move the reader to the next chapter."""
        # Chapters are ordered backwards.
        self.chapter = max(0, self.chapter - 1)
        self.page = 0

        chapter = self.chapters[self.chapter]
        self.pages = await chapter.pages(self.session)
        await interaction.response.edit_message(content=self.pages[self.page])

    @discord.ui.button(label="Previous Chapter", row=1)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Move the reader to the previous chapter."""

        self.chapter = min(len(self.chapters) - 1, self.chapter + 1)
        self.page = 0

        chapter = self.chapters[self.chapter]
        self.pages = await chapter.pages(self.session)
        await interaction.response.edit_message(content=self.pages[self.page])
