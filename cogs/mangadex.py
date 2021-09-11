import backends.mangadex as mangadex
import utilities
import model

import discord.ext.commands as commands

class Mangadex(commands.Cog):
    """Bakerbot's implementation of the Mangadex API (v5)."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    @commands.group(invoke_without_subcommand=True)
    async def manga(self, ctx: commands.Context) -> None:
        """The parent command for the manga reader."""
        summary = ("You've encountered the Mangadex command group! "
                   "See `$help mangadex` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @manga.command()
    async def info(self, ctx: commands.Context, *, title: str) -> None:
        """Returns information about a specific manga."""
        async with ctx.typing():
            manga = await mangadex.Backend.search(title, 1)
            author = await manga.author()
            cover = await manga.cover()

        embed = utilities.Embeds.standard()
        embed.set_footer(text="Powered by the Mangadex API.", icon_url=utilities.Icons.INFO)
        embed.title = f"Mangadex: {manga.title}"
        embed.description = "No description available."
        embed.url = f"{mangadex.Backend.client}/title/{manga.identifier}"

        if manga.description is not None:
            stripped = manga.description.strip()
            embed.description = f"{stripped[0:256]}..." if len(stripped) > 256 else stripped

        if cover is not None:
            embed.set_thumbnail(url=cover)

        embed.add_field(name="🗿  Author", value=author)
        genres = ", ".join(tag.name for tag in manga.tags) or "No genres available."
        tgenre = "📖  Genres" if len(manga.tags) > 1 else "📖  Genre"
        embed.add_field(name=tgenre, value=genres)

        demographic = utilities.Text.titlecase(manga.demographic, "Unknown demographic.")
        status = utilities.Text.titlecase(manga.status, "Unknown status.")
        rating = utilities.Text.titlecase(manga.content_rating)
        last_chapter = utilities.Text.titlecase(manga.last_chapter, "Not available.")
        embed.add_field(name="🤺  Demographic", value=demographic)
        embed.add_field(name="✍🏼  Status", value=status)
        embed.add_field(name="👹  Content Rating", value=rating)
        embed.add_field(name="🏗️  New Chapter(s)", value=last_chapter)
        await ctx.reply(embed=embed)

def setup(bot: model.Bakerbot) -> None:
    cog = Mangadex(bot)
    bot.add_cog(cog)
