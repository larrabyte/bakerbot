import discord.app_commands as application
import discord.ext.commands as commands

import database
import discord
import colours
import typing
import icons
import bot
import re

def package(message: discord.Message) -> discord.Embed:
    """Package a message into a starboard embed."""
    embed = discord.Embed(colour=colours.REGULAR, timestamp=message.created_at)
    embed.set_footer(text="NUTS!", icon_url=icons.INFO)

    if message.embeds and (source := message.embeds[0]).type == "rich":
        embed.set_author(name=source.author.name, icon_url=source.author.icon_url)
        embed.description = source.description
    else:
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url
        )

        embed.description = message.content

    if message.embeds and (source := message.embeds[0]).type == "image" and source.url not in re.findall(r"\|\|(.+?)\|\|", message.content):
        embed.set_image(url=source.url)

    embed.add_field(name="Original", value=f"[Jump!]({message.jump_url})")
    if (ref := message.reference) is not None and isinstance((res := ref.resolved), discord.Message):
        embed.add_field(name="Replying to...", value=f"[{res.author}]({res.jump_url})")

    if message.attachments:
        file = message.attachments[0]
        extensions = ("png", "jpeg", "jpg", "gif", "webp")

        if not file.is_spoiler() and file.url.lower().endswith(extensions):
            embed.set_image(url=file.url)

        elif file.is_spoiler():
            embed.add_field(
                name="Attachment",
                value=f"||[{file.filename}]({file.url})||",
                inline=False
            )

        else:
            embed.add_field(
                name="Attachment",
                value=f"[{file.filename}]({file.url})",
                inline=False
            )

    if message.stickers:
        embed.set_image(url=message.stickers[0].url)

    return embed

@application.guild_only()
class Starboard(commands.GroupCog):
    def __init__(self, bot: bot.Bot):
        super().__init__()
        self.bot = bot

    @application.command(description="Query the current status of the starboard.")
    async def status(self, interaction: discord.Interaction):
        guild = typing.cast(discord.Guild, interaction.guild)
        config = await database.GuildConfiguration.read(self.bot.pool, guild.id)

        if config is None:
            return await interaction.response.send_message(
                "This guild does not have a starboard configuration.\n"
                "Consider executing `/starboard set` to initialise one."
            )

        threshold = config.starboard_reaction_threshold
        channel = self.bot.get_channel(config.starboard_channel_id) if config.starboard_channel_id is not None else None
        reaction = discord.utils.escape_markdown(config.starboard_reaction_string) if config.starboard_reaction_string is not None else None
        status = "enabled" if threshold is not None and channel is not None and reaction is not None else "disabled"

        await interaction.response.send_message(
            f"The starboard is currently **{status}**.\n"
            f"- Reaction threshold: {threshold if threshold is not None else 'not set.'}\n"
            f"- Destination channel: {channel.mention if isinstance(channel, discord.abc.Messageable) else 'not set/invalid.'}\n"
            f"- Reaction: {reaction if reaction is not None else 'not set.'}",
            suppress_embeds=True
        )

    @application.command(description="Modify the current starboard configuration.")
    @application.describe(threshold="The number of reactions required to send a message to the starboard.  0 disables the starboard.")
    @application.describe(channel="The channel to send starboarded messages to.")
    @application.describe(emote="The emote (either as a Unicode character or custom ID) required to \"star\" a message.")
    async def set(self, interaction: discord.Interaction, threshold: application.Range[int, 0, None], channel: discord.TextChannel, emote: str):
        guild = typing.cast(discord.Guild, interaction.guild)
        config = database.GuildConfiguration(guild.id, threshold, channel.id, emote.strip())
        await config.write(self.bot.pool)
        await interaction.response.send_message("Guild configuration saved.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Global starboard reaction handler."""
        if payload.guild_id is None or (config := await database.GuildConfiguration.read(self.bot.pool, payload.guild_id)) is None:
            return

        threshold = config.starboard_reaction_threshold
        identifier = config.starboard_channel_id
        target = config.starboard_reaction_string

        if threshold is None or identifier is None or target is None or payload.channel_id == identifier:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            return

        message = await channel.fetch_message(payload.message_id)
        reactions = sum(str(reaction.emoji) == target for reaction in message.reactions)

        if reactions >= threshold:
            if (cache := await database.StarboardMessage.read(self.bot.pool, payload.message_id)) is not None:
                cache.reactions = reactions
            elif isinstance((starboard := self.bot.get_channel(identifier)), discord.abc.Messageable):
                await starboard.send(embed=package(message))

            result = cache or database.StarboardMessage(
                payload.message_id,
                message.author.id,
                payload.channel_id,
                payload.guild_id,
                message.reference.message_id if message.reference is not None else None,
                message.created_at,
                message.content,
                [attachment.url for attachment in message.attachments],
                [sticker.url for sticker in message.stickers],
                reactions
            )

            await result.write(self.bot.pool)
