import utilities
import model

from discord.ext import commands
import discord

class Configuration:
    def __init__(self, emote: discord.Emoji, channel: discord.TextChannel, threshold: int):
        self.threshold = threshold
        self.channel = channel
        self.emote = emote

class Starboard(commands.Cog):
    """Bakerbot's implementation of a starboard."""
    def __init__(self, bot: model.Bakerbot):
        self.bot = bot
        self.map = {}

    def register(self, guild_id: int, emote_id: int, channel_id: int, threshold: int) -> None:
        """Registers a guild for starboard functionality."""
        guild = self.bot.get_guild(guild_id)
        emote = self.bot.get_emoji(emote_id)
        channel = self.bot.get_channel(channel_id)

        if None not in (guild, emote, channel):
            self.map[guild_id] = Configuration(emote, channel, threshold)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """If we encounter a message with a special reaction, send it to that guild's starboard channel."""
        if payload.guild_id not in self.map:
            return

        configuration = self.map[payload.guild_id]
        if payload.channel_id == configuration.channel.id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = next((r for r in message.reactions if r.emoji == configuration.emote), None)
        if reaction is not None and reaction.count >= configuration.threshold:
            package = utilities.Embeds.package(message)
            await configuration.channel.send(embed=package)

def setup(bot: model.Bakerbot) -> None:
    cog = Starboard(bot)
    bot.add_cog(cog)
