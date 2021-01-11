from discord.ext import commands
import disputils as dsp
import datetime as dt
import discord
import aiohttp
import re

class MangadexError(commands.CommandError):
    NO_MANGA_FOUND = 0
    HTTP_ERROR     = 1

    def __init__(self, exception_type: int, message: str=None) -> None:
        self.exception_type = exception_type
        self.message = message

    def __str__(self) -> str:
        if self.exception_type == self.NO_MANGA_FOUND:
            return f"MangadexError({self.exception_type}) raised: No manga found."
        elif self.exception_type == self.HTTP_ERROR:
            return f"MangadexError({self.exception_type}) raised: HTTP {self.message}."

class Mangadex(commands.Cog, name="mangadex"):
    """Mangadex API implementation in Python."""
    def __init__(self, bot: commands.Bot) -> None:
        bot.loop.create_task(self.startup())
        self.bot = bot

    async def startup(self) -> None:
        """Manages any cog prerequisites."""
        await self.bot.wait_until_ready()
        self.util = self.bot.get_cog("utilities")
        self.tags = await self.fetch_jsondata(f"https://mangadex.org/api/v2/tag")

    async def fetch_jsondata(self, url: str) -> dict:
        """Wrapper for aiohttp to fetch JSON data from a URL."""
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                if resp.status != 200: raise MangadexError(MangadexError.HTTP_ERROR, resp.status)
                data = await resp.json()
                return data["data"]

    @commands.command()
    async def reader(self, ctx: commands.Context, mangaid: int) -> None:
        """Read a manga using its Mangadex ID."""
        metadata = await self.fetch_jsondata(f"https://mangadex.org/api/v2/manga/{mangaid}/chapters")
        chapters = [chapter for chapter in metadata["chapters"] if chapter["language"] == "gb"]
        chapters.sort(key=lambda chapter: float(chapter["chapter"]) if chapter["chapter"] else 0)
        chapters = [chapter["id"] for chapter in chapters]

        chapter = await self.fetch_jsondata(f"https://mangadex.org/api/v2/chapter/{chapters[0]}")
        embeds = []

        for index, pages in enumerate(chapter["pages"]):
            embed = discord.Embed(colour=self.util.regular_colour)
            embed.set_image(url=f"{chapter['serverFallback']}{chapter['hash']}/{chapter['pages'][index]}")
            embed.set_footer(text=f"{chapter['mangaTitle']}")
            embeds.append(embed)

        paginator = dsp.BotEmbedPaginator(ctx, embeds)
        await paginator.run()
        await ctx.message.delete()

    @commands.command()
    async def manga(self, ctx: commands.Context, mangaid: int) -> None:
        """Get a manga using its Mangadex ID. Searching is unavailable due to a login requirement imposed by Mangadex."""
        manga = await self.fetch_jsondata(f"https://mangadex.org/api/v2/manga/{mangaid}")
        embed = discord.Embed(title="Bakerbot: Mangadex API request.",
                              description=f"[{manga['title']}](https://mangadex.org/title/{mangaid})",
                              colour=self.util.regular_colour,
                              timestamp=dt.datetime.utcnow())

        embed.add_field(name="👁️  Views", value=f"{manga['views']:,} views")
        embed.add_field(name="🔖  Followers", value=f"{manga['follows']:,} followers")
        embed.add_field(name="⭐  Rating", value=f"{manga['rating']['bayesian']}/10 ({manga['rating']['users']:,} votes)")
        embed.add_field(name="✍️  Authors", value=", ".join(manga["author"]))

        genres = [f"`{self.tags[str(tag)]['name']}`" for tag in manga["tags"]]
        genres[2::3] = [f"{tag}\n" for tag in genres[2::3]]
        embed.add_field(name="💴  Themes and Genres", value=" ".join(genres) if genres else "`Unknown`")

        embed.set_footer(text=f"To start reading, type $reader <mangaid>.", icon_url=self.util.note_icon)
        if manga["mainCover"]: embed.set_thumbnail(url=manga["mainCover"])
        await ctx.send(embed=embed)

def setup(bot): bot.add_cog(Mangadex(bot))
