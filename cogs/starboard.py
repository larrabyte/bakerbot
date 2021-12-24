import utilities
import database
import model

from discord.ext import commands
import typing as t
import pymongo
import discord

class Starboard(commands.Cog):
    """Bakerbot's implementation of a starboard."""
    def __init__(self, bot: model.Bakerbot):
        self.bot = bot

    def get_emoji(self, message: discord.Message, identifier: int) -> t.Optional[discord.Reaction]:
        """Return the reaction with an ID of `identifier` or None."""
        for reaction in message.reactions:
            if isinstance(reaction.emoji, discord.Emoji) and reaction.emoji.id == identifier:
                return reaction

        return None

    @commands.group(invoke_without_subcommand=True)
    async def starboard(self, ctx: commands.Context) -> None:
        """The parent command for the starboard."""
        summary = ("You've encountered Bakerbot's starboard implementation! "
                   "See `$help starboard` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @starboard.command()
    async def status(self, ctx: commands.Context) -> None:
        """Query this guild's starboard status."""
        config = await database.GuildConfiguration.ensure(self.bot.db, ctx.guild.id)
        embed = utilities.Embeds.standard()
        icon = ctx.guild.icon.url if ctx.guild.icon is not None else None
        embed.set_author(name=ctx.guild.name, icon_url=icon)

        starboard = self.bot.db["starboarded_messages"]
        document = await starboard.find_one({"guild_id": ctx.guild.id}, {"_id": False}, sort=[("_id", pymongo.DESCENDING)])
        timestamp = "undefined"

        if document is not None:
            last = database.StarboardMessage(**document)
            timestamp = last.timestamp.strftime("%d/%m/%Y")

        embed.set_footer(text=f"Last starboard message timestamp: {timestamp}", icon_url=utilities.Icons.INFO)

        embed.description = f" • Current starboard threshold: {config.starboard_threshold}."
        channel = self.bot.get_channel(config.starboard_channel_id)
        emoji = self.bot.get_emoji(config.starboard_emoji_id)
        channel_str = channel.mention if channel is not None else "undefined."
        emoji_str = str(emoji) if emoji is not None else "undefined."

        embed.description += f"\n • Current starboard channel: {channel_str}"
        embed.description += f"\n • Current starboard emote: {emoji_str}"
        await ctx.reply(embed=embed)

    @starboard.command()
    async def enable(self, ctx: commands.Context) -> None:
        """Enable this guild's starboard."""
        config = await database.GuildConfiguration.ensure(self.bot.db, ctx.guild.id)

        if None in (config.starboard_channel_id, config.starboard_emoji_id):
            return await ctx.reply("Please set the channel and/or emoji before enabling the starboard.")

        config.starboard_enabled = True
        await config.write(self.bot.db)
        await ctx.reply("Starboard enabled.")

    @starboard.command()
    async def disable(self, ctx: commands.Context) -> None:
        """Disables this guild's starboard."""
        config = await database.GuildConfiguration.ensure(self.bot.db, ctx.guild.id)
        config.starboard_enabled = False
        await config.write(self.bot.db)
        await ctx.reply("Starboard disabled.")

    @starboard.command()
    async def threshold(self, ctx: commands.Context, threshold: t.Optional[int]) -> None:
        """Set or read this guild's starboard threshold."""
        config = await database.GuildConfiguration.ensure(self.bot.db, ctx.guild.id)

        if threshold is None:
            return await ctx.reply(f"Current starboard threshold: {config.starboard_threshold}")

        config.starboard_threshold = threshold
        await config.write(self.bot.db)
        await ctx.reply(f"Starboard threshold set to {threshold} reaction(s).")

    @starboard.command()
    async def channel(self, ctx: commands.Context, channel: t.Optional[discord.TextChannel]) -> None:
        """Set or read this guild's starboard channel."""
        config = await database.GuildConfiguration.ensure(self.bot.db, ctx.guild.id)
        configured = self.bot.get_channel(config.starboard_channel_id)

        if channel is None:
            invalid = f"Starboard channel is either invalid or unset. Currently stored channel ID: {config.starboard_channel_id}"
            valid = f"Current starboard channel: {configured.mention}"
            return await ctx.reply(invalid if configured is None else valid)

        config.starboard_channel_id = channel.id
        await config.write(self.bot.db)
        await ctx.reply(f"Starboard channel set to {channel.mention}.")

    @starboard.command()
    async def emote(self, ctx: commands.Context, emoji: t.Optional[discord.Emoji]) -> None:
        """Set or read this guild's starboard emote."""
        config = await database.GuildConfiguration.ensure(self.bot.db, ctx.guild.id)
        configured = self.bot.get_emoji(config.starboard_emoji_id)

        if emoji is None:
            invalid = f"Starboard emoji is either invalid or unset. Currently stored emoji ID: {config.starboard_emoji_id}"
            valid = f"Current starboard emoji: {configured}"
            return await ctx.reply(invalid if configured is None else valid)

        config.starboard_emoji_id = emoji.id
        await config.write(self.bot.db)
        await ctx.reply(f"Starboard emoji set to {emoji}.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """Global starboard reaction handler."""
        config = await database.GuildConfiguration.get(self.bot.db, payload.guild_id)
        if config is not None or not config.starboard_ready() or payload.channel_id == config.starboard_channel_id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = self.get_emoji(message, config.starboard_emoji_id)

        if reaction is not None and reaction.count >= config.starboard_threshold:
            cache = await database.StarboardMessage.get(self.bot.db, payload.message_id)

            if cache is not None:
                # If the message is already in the database, update it and don't send a new message.
                cache.reaction_count = reaction.count
            else:
                # Otherwise, send a message to the starboard channel.
                embed = utilities.Embeds.package(message)
                starboard = self.bot.get_channel(config.starboard_channel_id)
                await starboard.send(embed=embed)

            # Write either the updated version or new StarboardMessage instance to the database.
            sbmsg = cache or (await database.StarboardMessage.new(message, reaction.count))
            await sbmsg.write(self.bot.db)

def setup(bot: model.Bakerbot) -> None:
    if bot.db is not None:
        cog = Starboard(bot)
        bot.add_cog(cog)
