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

class Starboard(commands.GroupCog):
    def __init__(self, bot: bot.Bot):
        super().__init__()
        self.bot = bot

    # @application.guild_only() doesn't work in subcommands.
    @application.command(description="Query the current status of the starboard.")
    async def status(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message("This command must be executed in a guild.")

        config = await database.GuildConfiguration.read(self.bot.pool, interaction.guild.id)

        if config is None:
            return await interaction.response.send_message(
                "This guild does not have a starboard configuration.\n"
                "Consider executing `/starboard set` to initialise one."
            )

        status = "enabled" if config.starboard_configured() else "disabled."
        threshold = config.starboard_reaction_threshold or "not set."

        channel = self.bot.get_channel(config.starboard_channel_id or 0)
        mention = channel.mention if isinstance(channel, discord.abc.Messageable) else "not set."

        reaction = discord.utils.escape_markdown(config.starboard_reaction_string or "not set.")

        await interaction.response.send_message(
            f"The starboard is currently **{status}**.\n"
            f"- Reaction threshold: {threshold}\n"
            f"- Destination channel: {mention}\n"
            f"- Reaction: {reaction}",
            suppress_embeds=True
        )

    @application.command(description="Modify the current starboard configuration.")
    @application.describe(threshold="The number of reactions required to send a message to the starboard.  0 disables the starboard.")
    @application.describe(channel="The channel to send starboarded messages to.")
    @application.describe(emote="The emote (either as a Unicode character or custom ID) required to \"star\" a message.")
    async def set(self, interaction: discord.Interaction, threshold: application.Range[int, 0, None], channel: discord.TextChannel, emote: str):
        if interaction.guild is None:
            return await interaction.response.send_message("This command must be executed in a guild.")

        config = database.GuildConfiguration(interaction.guild.id, threshold, channel.id, emote.strip())
        await config.write(self.bot.pool)
        await interaction.response.send_message("Guild configuration saved.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Global starboard reaction handler."""
        if payload.guild_id is None:
            return

        config = await database.GuildConfiguration.read(self.bot.pool, payload.guild_id)
        if config is None or not config.starboard_configured() or payload.channel_id == config.starboard_channel_id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.abc.Messageable):
            return

        message = await channel.fetch_message(payload.message_id)
        reactions = sum(str(reaction.emoji) == config.starboard_reaction_string for reaction in message.reactions)
        threshold = typing.cast(int, config.starboard_reaction_threshold)

        if reactions >= threshold:
            cache = await database.StarboardMessage.read(self.bot.pool, payload.message_id)

            if cache is not None:
                # If the message is already in the database, then don't send a new message.
                cache.reactions = reactions
            else:
                embed = package(message)
                id = typing.cast(int, config.starboard_channel_id)
                starboard = self.bot.get_channel(id)

                assert isinstance(starboard, discord.abc.Messageable)
                await starboard.send(embed=embed)

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
