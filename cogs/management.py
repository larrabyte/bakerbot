import utilities
import database
import model

from discord.ext import commands
import typing as t
import discord
import random

class Management(commands.Cog):
    """Handles configuration of guild-specific settings."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    @commands.group(invoke_without_subcommands=True)
    async def guild(self, ctx: commands.Context) -> None:
        """The parent command for guild management."""
        summary = ("You've encountered Bakerbot's guild-specific management system! "
                   "See `$help management` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @guild.command()
    async def ignore(self, ctx: commands.Command, channels: commands.Greedy[discord.TextChannel]) -> None:
        """Makes Bakerbot ignore/unignore messages from certain channels."""
        config = await database.GuildConfiguration.ensure(self.bot.db, ctx.guild.id)

        if len(channels) > 0:
            # Add channels to the ignore set only if they're
            # not already in it. Otherwise, remove them.
            ignore_set = set(config.ignored_channels)
            for channel in [c.id for c in channels]:
                if channel in ignore_set:
                    ignore_set.remove(channel)
                else:
                    ignore_set.add(channel)

            config.ignored_channels = list(ignore_set)
            await config.write(self.bot.db)

            if len(config.ignored_channels) > 0:
                text = f"Bakerbot will no longer respond to messages in these channels:\n"
                objects = [self.bot.get_channel(c) for c in config.ignored_channels]
                text += "\n".join(f" • {channel.mention}" for channel in objects)
            else:
                text = "Bakerbot will no longer ignore any channels in this guild."

        elif len(config.ignored_channels) > 0:
            # Otherwise, simply list the ignored channels for this guild.
            text = f"Bakerbot currently ignores these channels:\n"
            ignored = [self.bot.get_channel(identifier) for identifier in config.ignored_channels]
            text += "\n".join(f" • {channel.mention}" for channel in ignored)

        else:
            # If we actually aren't ignoring anything, just say that.
            text = "Bakerbot does not ignore any channels from this guild."

        await ctx.reply(text)

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
                    embed = utilities.Embeds.package(message)
                    await message.reply(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Calls relevant subroutines when a message is received."""
        await self.who_asked(message)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Calls relevant subroutines when a message is deleted."""
        await self.message_resender(message)

def setup(bot: model.Bakerbot) -> None:
    if bot.db is not None:
        cog = Management(bot)
        bot.add_cog(cog)
