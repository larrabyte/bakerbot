import discord.app_commands as application
import discord.ext.commands as commands
import starboard.tenor as tenor

import urllib.parse
import database
import aiohttp
import discord
import colours
import typing
import icons
import bot
import re

def sanitise(url: str | None) -> str | None:
    """Sanitise attachment URLs (eg. strip query parameters off of Discord CDN URLs)."""
    if url is None:
        return None

    scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url)

    return urllib.parse.urlunparse((
        scheme,
        netloc,
        path,
        params,
        query if netloc != "cdn.discordapp.com" else "",
        fragment
    ))

async def package(session: aiohttp.ClientSession, message: discord.Message) -> discord.Embed:
    """Package a message into a starboard embed."""
    package = discord.Embed(colour=colours.REGULAR, timestamp=message.created_at)
    package.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    package.set_footer(text="NUTS!", icon_url=icons.INFO)
    package.add_field(name="Original", value=f"[Jump!]({message.jump_url})")
    package.description = message.content

    if message.reference is not None and isinstance(message.reference.resolved, discord.Message):
        package.add_field(name="Replying to...", value=f"[{message.reference.resolved.author}]({message.reference.resolved.jump_url})")

    if (embed := next((embed for embed in message.embeds), None)) is not None:
        if embed.type == "rich":
            package.set_author(name=embed.author.name, icon_url=embed.author.icon_url)
            package.description = embed.description
        elif embed.type == "image" and embed.url not in re.findall(r"\|\|(.+?)\|\|", message.content):
            package.set_image(url=embed.url)
            package.description = ""
        elif embed.type == "gifv" and embed.url is not None and (gif := await tenor.raw(session, embed.url)) is not None:
            package.set_image(url=gif)
            package.description = ""

    if (file := next((attachment for attachment in message.attachments), None)) is not None:
        # Strip attachment signature fields so that Discord renders attachments.
        assert (url := sanitise(file.url)) is not None

        if not file.is_spoiler() and url.lower().endswith(("png", "jpeg", "jpg", "gif", "webp")):
            package.set_image(url=url)
        elif file.is_spoiler():
            package.add_field(name="Attachment", value=f"||[{file.filename}]({url})||", inline=False)
        else:
            package.add_field(name="Attachment", value=f"[{file.filename}]({url})", inline=False)

    if (embed := next((sticker for sticker in message.stickers), None)) is not None:
        package.set_image(url=embed.url)

    return package

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
        reaction = next(filter(lambda reaction: str(reaction.emoji) == target, message.reactions), None)

        if reaction is None:
            return

        if reaction.count >= threshold:
            if (cache := await database.StarboardMessage.read(self.bot.pool, payload.message_id)) is not None:
                cache.reactions = reaction.count
            elif isinstance((starboard := self.bot.get_channel(identifier)), discord.abc.Messageable):
                await starboard.send(embed=await package(self.bot.session, message))

            result = cache or database.StarboardMessage(
                payload.message_id,
                message.author.id,
                payload.channel_id,
                payload.guild_id,
                message.reference.message_id if message.reference is not None else None,
                message.created_at,
                message.content,
                [url for attachment in message.attachments if (url := sanitise(attachment.url)) is not None],
                [sticker.url for sticker in message.stickers],
                reaction.count
            )

            await result.write(self.bot.pool)
