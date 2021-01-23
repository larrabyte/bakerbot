from libs.utilities import Embeds, Colours, Icons, Paginator
from libs.mangadex import Mangadex
from libs.models import Bakerbot
from discord.ext import commands

import discord
import asyncio

class Media(commands.Cog):
    """Experimental media viewer. Currently home to the manga reader."""
    def __init__(self, bot: Bakerbot) -> None:
        self.bot = bot

    @commands.group(invoke_without_subcommand=True)
    async def manga(self, ctx: commands.Context) -> None:
        """The parent command for the manga reader."""
        if ctx.invoked_subcommand is None:
            # Since there was no subcommand, inform the user about the manga reader and its subcommands.
            desc = ("Welcome to the experimental manga reader. Support is currently limited to "
                    "numerical IDs as Mangadex imposes a login requirement for searching.\n"
                    "See `$help media` for a full list of available subcommands.")

            embed = discord.Embed(description=desc, colour=Colours.regular, timestamp=Embeds.now())
            embed.set_footer(text="Powered by the Mangadex API (v2).", icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @manga.command()
    async def info(self, ctx: commands.Context, id: int) -> None:
        """Get information about a manga given its Mangadex identifier."""
        async with ctx.typing():
            if (manga := await Mangadex.create(id=id, lang="gb")) is None:
                fail = Embeds.status(success=False, desc="No manga found.")
                return await ctx.send(embed=fail)

        embed = discord.Embed(description=f"[{manga.title}](https://mangadex.org/title/{manga.id})",
                              colour=Colours.regular,
                              timestamp=Embeds.now())

        embed.add_field(name="👁️  Views", value=f"{manga.views:,} views")
        embed.add_field(name="🔖  Followers", value=f"{manga.follows:,} followers")
        embed.add_field(name="⭐  Rating", value=f"{manga.ratings.bayesian}/10 ({manga.ratings.users:,} votes)")
        embed.add_field(name="✍️  Authors", value=manga.authors)
        embed.add_field(name="💴  Themes and Genres", value=manga.tags)

        embed.set_footer(text=f"To start reading, type $manga read <id>.", icon_url=Icons.info)
        if manga.cover: embed.set_thumbnail(url=manga.cover)
        await ctx.send(embed=embed)

    @manga.command()
    async def read(self, ctx: commands.Context, id: int) -> None:
        """Start reading manga! Takes a Mangadex ID to start."""
        async with ctx.typing():
            if (manga := await Mangadex.create(id=id, lang="gb")) is None:
                fail = Embeds.status(success=False, desc="No manga found.")
                return await ctx.send(embed=fail)
            elif not manga.chapters:
                fail = Embeds.status(success=False, desc="No chapters available.")
                return await ctx.send(embed=fail)

        # Setup the paginator and a template embed for listing chapters.
        paginator = Paginator(embeds=None, message=None)
        paginator.template = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
        paginator.template.set_footer(text="Reply with the chapter's ID to start reading.", icon_url=Icons.info)

        for chapter in manga.chapters:
            text = f"`{chapter.id}` -> [{chapter}](https://mangadex.org/chapter/{chapter.id})\n"
            paginator.add_description(line=text)

        # Start the paginator in the background.
        await paginator.start(ctx=ctx, users=ctx.author)
        check = lambda m: m.author == ctx.author and m.reference \
                and m.reference.message_id == paginator.message.id

        try: # Try awaiting a reply from the user before converting it into a valid chapter.
            message = await self.bot.wait_for("message", timeout=360, check=check)
            chapter = next((c for c in manga.chapters if c.id == int(message.content)))
        except (ValueError, StopIteration, asyncio.TimeoutError) as e:
            if isinstance(e, ValueError):
                desc = "That isn't even a number."
                await message.delete()
            elif isinstance(e, StopIteration):
                desc = "No chapter found with that ID."
                await message.delete()
            elif isinstance(e, asyncio.TimeoutError):
                desc = "Timeout reached (360 seconds)."

            await paginator.stop()
            fail = Embeds.status(success=False, desc=desc)
            return await paginator.message.edit(embed=fail)

        # Cleanup the paginator.
        await message.delete()
        await paginator.stop()

        async for image in chapter.images():
            embed = discord.Embed(colour=Colours.regular)
            embed.set_footer(text=chapter, icon_url=ctx.author.avatar_url)
            embed.set_image(url=image)
            paginator.embeds.append(embed)

        await paginator.start(ctx=ctx, users=ctx.author)

def setup(bot): bot.add_cog(Media(bot))
