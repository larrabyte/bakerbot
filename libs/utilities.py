from discord.ext import commands

import datetime as dt
import typing as t
import discord
import asyncio
import re

class Colours:
    regular = 0xF5CC00  # Used for everything else.
    success = 0x00C92C  # Used for successful queries.
    failure = 0xFF3300  # Used for error messages.
    gaming = 0x0095FF   # Used for game-related commands.

class Regexes:
    # Used to detect URLs.
    urls = re.compile(r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))")
    markdown = re.compile(r"([*_~`|>])")

    @classmethod
    def url(cls, string: str) -> bool:
        # Return whether a given string is a URL or not.
        return bool(re.match(cls.urls, string))

    @classmethod
    def escapemd(cls, string: str) -> str:
        # Return a string with escaped markdown characters.
        return cls.markdown.sub(r"\\\1", string)

class Icons:
    tick = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Flat_tick_icon.svg/500px-Flat_tick_icon.svg.png"
    cross = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Flat_cross_icon.svg/500px-Flat_cross_icon.svg.png"
    info = "https://icon-library.com/images/info-icon-svg/info-icon-svg-5.jpg"
    illuminati = "https://upload.wikimedia.org/wikipedia/commons/a/a9/Illuminati_triangle_eye.png"
    rfa = "https://upload.wikimedia.org/wikipedia/commons/4/40/Radio_Free_Asia_%28logo%29.png"
    wikipedia = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/500px-Wikipedia-logo-v2.svg.png"

class Embeds:
    @staticmethod
    def status(success: bool, desc: str) -> discord.Embed:
        # Select colours/icon/title for success or failure embeds.
        status = "Operation successful!" if success else "Operation failed!"
        colour = Colours.success if success else Colours.failure
        icon = Icons.tick if success else Icons.cross

        # Create embed and set relevant data before returning.
        embed = discord.Embed(colour=colour, timestamp=dt.datetime.utcnow())
        embed.set_footer(text=status, icon_url=icon)
        if desc is not None: embed.description = desc
        return embed

    @staticmethod
    def now() -> dt.datetime:
        # Return current UTC time.
        return dt.datetime.utcnow()

class Choices:
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
    special = ["❌"]

    @classmethod
    async def prompt(cls, ctx: commands.Context, embed: discord.Embed, n: int, author_only: bool) -> t.Optional[int]:
        # List of available reactions, including any special control emojis.
        options = list(cls.emojis)[:min(n, len(cls.emojis))] + Choices.special

        # Lambda check to ensure that the reaction/author/message is correct.
        check = lambda e, u: e.emoji in options and u == ctx.author and e.message.id == msg.id \
                if author_only else lambda e, u: e.emoji in options and e.message.id == msg.id

        # Send the embed and add reactions.
        msg = await ctx.send(embed=embed)
        for emoji in options: await msg.add_reaction(emoji)

        try: # Await a response from the user.
            reaction, user = await ctx.bot.wait_for("reaction_add", timeout=30, check=check)
        except asyncio.TimeoutError:
            fail = Embeds.status(success=False, desc="Timeout reached (30 seconds).")
            await msg.clear_reactions()
            await msg.edit(embed=fail)
            return None

        # Get the corresponding value.
        await msg.delete()
        if reaction.emoji == Choices.special[0]:
            return None

        return Choices.emojis.index(reaction.emoji)

class Paginator:
    emojis = ["⏮", "◀", "▶", "⏭", "⏹"]

    def __init__(self, embeds: t.Optional[t.List[discord.Embed]], message: t.Optional[discord.Message]) -> None:
        self.embeds = embeds if embeds else []
        self.message = message
        self.index = 0

        # Can't be initialised at startup.
        self.users: t.List[discord.User] = None
        self.template: discord.Embed = None
        self.task: asyncio.Task = None

    @property
    def newembed(self) -> discord.Embed:
        # Return a fresh template copy.
        fresh = self.template.copy()
        self.embeds.append(fresh)
        return fresh

    def add_description(self, line: str) -> None:
        # Add lines while respecting the description character limit.
        current = self.embeds[-1] if self.embeds else self.newembed
        if len(current.description) + len(line) > 2048:
            current = self.newembed

        if current.description == discord.Embed.Empty:
            current.description = line
        else: current.description += line

    def add_field(self, name: str, value: str, inline: bool) -> None:
        # Add fields while respecting the embed's character limit.
        current = self.embeds[-1] if self.embeds else self.newembed
        if len(current) + len(name) + len(value) > 6000 or len(current.fields) > 24:
            current = self.newembed

        current.add_field(name=name, value=value if len(value) < 1024 else f"{value[0:1021]}...", inline=inline)

    async def start(self, ctx: commands.Context, users: t.Union[discord.User, t.List[discord.User]]) -> None:
        # Format our embeds before starting the paginator.
        for index, embed in enumerate(self.embeds, 1):
            if embed.footer.text != discord.Embed.Empty:
                footer = f"{embed.footer.text} • "
            else: footer = ""

            footer += f"Page {index}/{len(self.embeds)}"
            embed.set_footer(text=footer, icon_url=embed.footer.icon_url)

        # Makes sure self.message is a valid Message object.
        if self.message is None:
            self.message = await ctx.send(embed=self.embeds[0])
        else: await self.message.edit(embed=self.embeds[0])

        # Create a task instead of using await so it doesn't block.
        self.users = users if isinstance(users, list) else [users]
        self.task = ctx.bot.loop.create_task(self.run(ctx=ctx))

    async def stop(self) -> None:
        # Cancel the paginator's task and (mostly) reset its internal state.
        await self.message.clear_reactions()
        self.task.cancel()
        self.users = None
        self.embeds = []
        self.index = 0

    async def run(self, ctx: commands.Context) -> None:
        # Start the paginator. Only stops upon await self.stop() or a stop reaction.
        check = lambda r, u: r.message.id == self.message.id and r.emoji in Paginator.emojis and u in self.users
        for emoji in Paginator.emojis: await self.message.add_reaction(emoji)

        while True:
            reaction, user = await ctx.bot.wait_for("reaction_add", check=check)

            # Perform actions depending on reaction.
            if reaction.emoji == Paginator.emojis[0]:
                self.index = 0
            elif reaction.emoji == Paginator.emojis[1]:
                if 0 <= self.index - 1 < len(self.embeds):
                    self.index -= 1
            elif reaction.emoji == Paginator.emojis[2]:
                if 0 <= self.index + 1 < len(self.embeds):
                    self.index += 1
            elif reaction.emoji == Paginator.emojis[3]:
                self.index = len(self.embeds) - 1
            elif reaction.emoji == Paginator.emojis[4]:
                await self.message.clear_reactions()
                embed = Embeds.status(success=True, desc="Paginator closed.")
                return await self.message.edit(embed=embed)

            # Edit the message to reflect any changes.
            await self.message.edit(embed=self.embeds[self.index])
            await self.message.remove_reaction(reaction, user)
