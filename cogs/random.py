import utilities
import database
import model

from discord.ext import commands
import typing as t
import discord
import asyncio
import random

class Random(commands.Cog):
    """Random ideas that I come up with every now and again."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    @commands.group(invoke_without_subcommand=True, aliases=["discord"])
    async def discordo(self, ctx: commands.Context) -> None:
        """The parent command for Discord experiments."""
        summary = ("You've encountered Bakerbot's Discord experimentation lab! "
                   "See `$help random` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @discordo.command()
    async def typing(self, ctx: commands.Context) -> None:
        """Starts typing in every available text channel."""
        coroutines = [channel.trigger_typing() for channel in ctx.guild.text_channels]
        await asyncio.gather(*coroutines)

    @commands.command()
    async def nodelete(self, ctx: commands.Context, toggle: t.Optional[str]) -> None:
        """Controls the message persistence system."""
        config = await database.GuildConfiguration.ensure(self.bot.db, ctx.guild.id)
        enablers = ("on", "enable", "true")
        disablers = ("off", "disable", "false")

        if toggle is None:
            noun = "enabled" if config.message_resender_enabled else "disabled"
            return await ctx.reply(f"The message persistence system is currently {noun}.")

        if toggle.lower() in enablers:
            config.message_resender_enabled = True
            await ctx.reply("The message persistence system has been enabled.")
            await config.write(self.bot.db)
        elif toggle.lower() in disablers:
            config.message_resender_enabled = False
            await ctx.reply("The message persistence system has been disabled.")
            await config.write(self.bot.db)
        else:
            allowables = ", ".join(enablers + disablers)
            await ctx.reply(f"Invalid `toggle` parameter. Valid options are: {allowables}.")

    @commands.command()
    async def whoasked(self, ctx: commands.Context, toggle: t.Optional[str]) -> None:
        """Controls the message autoreply system."""
        config = await database.GuildConfiguration.ensure(self.bot.db, ctx.guild.id)
        enablers = ("on", "enable", "true")
        disablers = ("off", "disable", "false")

        if toggle is None:
            noun = "enabled" if config.who_asked_enabled else "disabled"
            return await ctx.reply(f"The message autoreply system is currently {noun}.")

        if toggle.lower() in enablers:
            config.who_asked_enabled = True
            await ctx.reply("The message autoreply system has been enabled.")
            await config.write(self.bot.db)
        elif toggle.lower() in disablers:
            config.who_asked_enabled = False
            await ctx.reply("The message autoreply system has been disabled.")
            await config.write(self.bot.db)
        else:
            allowables = ", ".join(enablers + disablers)
            await ctx.reply(f"Invalid `toggle` parameter. Valid options are: {allowables}.")

    async def who_asked(self, message: discord.Message) -> None:
        """Handles the "ok but who asked?" reply feature."""
        if message.author.id != self.bot.user.id and message.guild is not None:
            if (config := await database.GuildConfiguration.get(self.bot.db, message.guild.id)) is not None:
                if config.who_asked_enabled and random.randint(0, 1000) == 0:
                    await message.reply("ok but who asked?")

    async def message_resender(self, message: discord.Message) -> None:
        """Handles the message resending feature."""
        if message.author.id != self.bot.user.id and message.guild is not None:
            if (config := await database.GuildConfiguration.get(self.bot.db, message.guild.id)) is not None:
                if config.message_resender_enabled:
                    await self.sniper.resend(message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Calls relevant subroutines when a message is received."""
        await self.who_asked(message)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Calls relevant subroutines when a message is deleted."""
        await self.message_resender(message)

def setup(bot: model.Bakerbot) -> None:
    cog = Random(bot)
    bot.add_cog(cog)
