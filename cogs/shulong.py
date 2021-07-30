import discord.ext.commands as commands
import discord.ext.tasks as tasks
import typing as t
import discord
import asyncio
import random
import model

class Shulong(commands.Cog):
    """You can find scrumptious ideas from Shulong here."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.colours = bot.utils.Colours
        self.icons = bot.utils.Icons
        self.embeds = bot.utils.Embeds
        self.dyslexifier = Dyslexifier()
        self.bot = bot

    def cog_unload(self) -> None:
        """Ensure that all tasks are cancelled on unload."""
        self.dyslexifier.clear()

    @commands.group(invoke_without_subcommand=True)
    async def shulong(self, ctx: commands.Context) -> None:
        """The parent command for all things Shulong related."""
        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                # There is no subcommand: inform the user about Shulong commands.
                summary = """Hi! Welcome to the Shulong command group.
                            This cog houses commands that are scrumptious (his words).
                            See `$help shulong` for a full list of available subcommands."""

                embed = discord.Embed(colour=self.colours.regular, timestamp=self.embeds.now())
                embed.set_footer(text="Powered by sheer stupidity.", icon_url=self.icons.info)
                embed.description = summary
                await ctx.reply(embed=embed)
            else:
                # The subcommand was not valid: throw a fit.
                command = f"${ctx.command.name} {ctx.subcommand_passed}"
                summary = f"`{command}` is not a valid command."
                footer = "Try $help shulong for a full list of available subcommands."
                embed = self.embeds.status(False, summary)
                embed.set_footer(text=footer, icon_url=self.icons.cross)
                await ctx.reply(embed=embed)

    @shulong.command()
    async def random(self, ctx: commands.Context) -> None:
        """Generates and returns a random unicode code point in the CJK range."""
        codepoint = random.randint(0x4E00, 0x9FFF)
        character = chr(codepoint)
        await ctx.reply(character)

    @shulong.command()
    async def dyslexify(self, ctx: commands.Context, guild: discord.Guild) -> None:
        """Turns server layouts into mush. Surprisingly, doesn't leave logs behind!"""
        self.dyslexifier.add(guild)
        await ctx.reply(f"Dyslexifier started for `{guild.name}`!")

    @shulong.command()
    async def undyslexify(self, ctx: commands.Context, guild: discord.Guild) -> None:
        """Stop the dyslexifier."""
        self.dyslexifier.remove(guild)
        await ctx.reply(f"Dyslexifier removed for `{guild.name}`!")

class Dyslexifier:
    """A class that abstracts the dyslexification tasks."""
    def __init__(self) -> None:
        self.internal = {}

    def add(self, guild: discord.Guild) -> None:
        """Adds a dyslexifier task for `guild`."""
        cache = self.internal.get(guild.id, None)
        if cache is not None and not cache.is_running():
            cache.start(guild)

        task = tasks.loop(seconds=1)(self.routine)
        self.internal[guild.id] = task
        task.start(guild)

    def remove(self, guild: discord.Guild) -> None:
        """Removes the dyslexifier task for `guild`."""
        if guild.id in self.internal:
            task = self.internal[guild.id]
            task.cancel()

            del self.internal[guild.id]

    def clear(self) -> None:
        """Stops all dyslexifier tasks."""
        for task in self.internal.values():
            task.cancel()

        self.internal.clear()

    def get_random_category(self, guild: discord.Guild) -> t.Optional[discord.CategoryChannel]:
        """Returns a random category from the guild."""
        if not guild.categories:
            return None

        return random.choice(guild.categories)

    def get_random_index(self, guild: discord.Guild, category: t.Optional[discord.CategoryChannel]) -> int:
        """Returns an appropriate random index for a channel in `category`."""
        maximum = len(guild.channels) if category is None else len(category.channels)
        return random.randint(0, maximum)

    async def routine(self, guild: discord.Guild) -> None:
        """The dyslexification routine run for each guild."""
        for channel in guild.channels:
            category = self.get_random_category(guild)
            index = self.get_random_index(guild, category)
            await channel.move(beginning=True, category=category, index=index)
            await asyncio.sleep(1)

def setup(bot: model.Bakerbot) -> None:
    cog = Shulong(bot)
    bot.add_cog(cog)
