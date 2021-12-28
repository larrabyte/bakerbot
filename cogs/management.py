import utilities
import database
import model

from discord.ext import commands
import discord
import random

class Management(commands.Cog):
    """Here lie commands for managing guild-specific settings."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Ensure commands are being executed in a guild context."""
        return ctx.guild is not None

    @commands.group(invoke_without_subcommands=True)
    async def guild(self, ctx: commands.Context) -> None:
        """The parent command for guild management."""
        summary = ("You've encountered Bakerbot's guild-specific management system! "
                   "See `$help management` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @guild.command()
    async def ignore(self, ctx: commands.Command, channels: commands.Greedy[discord.TextChannel]) -> None:
        """Make Bakerbot ignore/respond to messages from certain channels."""
        config = await database.GuildConfiguration.ensure(ctx.guild.id)

        # Get the set of channels that are either already ignored or in the set of
        # to-be ignored channels, but not in both. Implements channel toggling.
        symmetric_difference = set(config.ignored_channels) ^ set(c.id for c in channels)
        config.ignored_channels = list(symmetric_difference)
        await config.write()

        if len(config.ignored_channels) > 0:
            list_modified = "Bakerbot will no longer respond to messages in these channels:\n"
            unchanged = "Bakerbot currently ignores messages in these channels:\n"
            text = list_modified if len(channels) > 0 else unchanged

            generator = (self.bot.get_channel(c) for c in config.ignored_channels if c is not None)
            text += "\n".join(f" • {channel.mention}" for channel in generator)
            await ctx.reply(text)

        elif len(channels) > 0:
            await ctx.reply("Bakerbot will no longer ignore messages from any channels in this guild.")

        else:
            await ctx.reply("Bakerbot does not currently ignore messages from any channels in this guild.")

    @guild.command()
    async def nodelete(self, ctx: commands.Context, toggle: bool | None) -> None:
        """Query the status of/enable/disable the message persistence system."""
        config = await database.GuildConfiguration.ensure(ctx.guild.id)

        if toggle is None:
            status = "enabled" if config.message_resender_enabled else "disabled"
            return await ctx.reply(f"The message persistence system is currently {status}.")

        config.message_resender_enabled = toggle
        word_to_use = "enabled" if toggle else "disabled"
        await config.write()
        await ctx.reply(f"The message persistence system has been {word_to_use}.")

    @guild.command()
    async def whoasked(self, ctx: commands.Context, toggle: bool | None) -> None:
        """Query the status of/enable/disable the message autoreply system."""
        config = await database.GuildConfiguration.ensure(ctx.guild.id)

        if toggle is None:
            status = "enabled" if config.who_asked_enabled else "disabled"
            return await ctx.reply(f"The message persistence system is currently {status}.")

        config.who_asked_enabled = toggle
        word_to_use = "enabled" if toggle else "disabled"
        await config.write()
        await ctx.reply(f"The message autoreply system has been {word_to_use}.")

    async def who_asked(self, message: discord.Message) -> None:
        """Handle the "ok but who asked?" reply feature."""
        if message.author.id != self.bot.user.id and message.guild is not None and database.Backend.db_object is not None:
            if (config := await database.GuildConfiguration.get(message.guild.id)) is not None:
                if config.who_asked_enabled and random.randint(0, 1000) == 0:
                    await message.reply("ok but who asked?")

    async def message_resender(self, message: discord.Message) -> None:
        """Handle the message resending feature."""
        if message.author.id != self.bot.user.id and message.guild is not None and database.Backend.db_object is not None:
            if (config := await database.GuildConfiguration.get(message.guild.id)) is not None:
                if config.message_resender_enabled:
                    embed = utilities.Embeds.package(message)
                    await message.reply(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Call relevant subroutines when a message is received."""
        await self.who_asked(message)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Call relevant subroutines when a message is deleted."""
        await self.message_resender(message)

def setup(bot: model.Bakerbot) -> None:
    cog = Management(bot)
    bot.add_cog(cog)

    async def on_message(message: discord.Message) -> None:
        """Bot-wide message handler to enforce guild-ignored channels."""
        if message.guild is not None and database.Backend.db_object is not None:
            config = await database.GuildConfiguration.get(message.guild.id)
            if config is not None and message.channel.id in config.ignored_channels:
                return

        await bot.process_commands(message)

    bot.on_message = on_message
