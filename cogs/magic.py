from backends import expcord
import utilities
import model
import os

from discord.ext import commands
import asyncio
import discord
import random

class Magic(commands.Cog):
    """You can find dumb ideas from Team Magic here."""
    def __init__(self, bot: model.Bakerbot):
        self.guild_id = bot.secrets['magic_guild_id']
        if bot.secrets.get('pns_enabled')  == True:
            self.pns = PersonalNotificationSystem(bot, self.guild_id)
        self.vc_targets = set()
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Ensure that commands are being run either by me or Team Magic."""
        owner = await self.bot.is_owner(ctx.author)
        return owner or (ctx.guild is not None and ctx.guild.id == self.guild_id)

    @commands.group(invoke_without_subcommand=True)
    async def magic(self, ctx: commands.Context) -> None:
        """The parent command for all things Team Magic related."""
        summary = ("You've encountered Team Magic's command group!"
                    "See `$help magic` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @magic.command()
    async def demux(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str) -> None:
        """A demultiplexing experiment using Discord webhooks."""
        endpoints = await channel.webhooks()
        user, avatar = ctx.author.display_name, self.bot.user.avatar.url
        tasks = [hook.send(message, username=user, avatar_url=avatar) for hook in endpoints]
        await asyncio.gather(*tasks)

    @magic.command()
    async def hookify(self, ctx: commands.Context, source: discord.TextChannel, destination: discord.TextChannel | None) -> None:
        """So it turns out you can have more than 10 webooks in a channel..."""
        hooks = await source.webhooks()

        if destination is None:
            webhooks = "\n".join(str(w.id) for w in hooks)
            return await ctx.reply(webhooks)

        for i in range(10 - len(hooks)):
            rand = random.randint(0, 2**32)
            name = f"bakerbot hook #{rand}"
            await expcord.Webhooks.create(source, name)

        # Refresh the list of hooks after we create more.
        for webhook in (await source.webhooks()):
            await expcord.Webhooks.move(webhook, destination)

        await ctx.reply("Webhooks created and moved.")

    @magic.command()
    async def gandalf(self, ctx: commands.Context, member: discord.Member) -> None:
        """Prevent a member from joining a voice channel."""
        mentions = discord.AllowedMentions.none()

        if member.id in self.vc_targets:
            self.vc_targets.remove(member.id)
            await ctx.reply(f"{member.mention} shall pass!", allowed_mentions=mentions)
        else:
            self.vc_targets.add(member.id)
            if member.voice is not None and member.voice.channel is not None:
                await member.move_to(None)

            await ctx.reply(f"{member.mention} shall not pass!", allowed_mentions=mentions)

    @magic.command()
    async def shitting(self, ctx: commands.Context) -> None:
        """Create a live shitting event."""
        if not ("discord-user-token" in self.bot.secrets and "discord-user-id" in self.bot.secrets):
            raise model.SecretNotFound("discord-user secrets not specified in secrets.json.")

        identifier = self.bot.secrets["discord-user-id"]
        token = self.bot.secrets["discord-user-token"]

        if ctx.guild.get_member(identifier) is None:
            fail = utilities.Embeds.status(False)
            fail.description = "Someone is missing..."
            fail.set_footer(text="Consider inviting them?", icon_url=utilities.Icons.CROSS)
            return await ctx.reply(embed=fail)

        if ctx.author.voice is None or ctx.author.voice.channel is None:
            fail = utilities.Embeds.status(False)
            fail.description = "You aren't in a voice channel!"
            return await ctx.reply(embed=fail)

        title = "live shitting event"
        description = "improved shitting setup for higher-quality shitting"
        remote = expcord.User(ctx, token, identifier)
        timestamp = discord.utils.utcnow()
        await remote.create_event(ctx.author.voice.channel, title, description, timestamp)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        """Team Magic-specific listener for preventing members from joining voice channels."""
        if member.id in self.vc_targets and after.channel is not None:
            await member.move_to(None)

class PersonalNotificationSystem:
    """A wrapper around `on_message()` just for the Big Dominic."""
    def __init__(self, bot: model.Bakerbot, guild_id: int) -> None:
        self.bot = bot
        self.guild = guild_id
        self.identifiers = set(bot.secrets.get('pns_subscribers',[]))
        bot.add_listener(self.on_message)

    def identifier_check(self, message: discord.Message) -> bool:
        """Check whether tracked users are mentioned or replied to."""
        return self.identifiers.intersection(set(member.id for member in message.mentions))

    async def post(self, message: discord.Message) -> None:
        """Post a message to each person's inbox."""
        for identifier in self.identifiers:
            if (user := self.bot.get_user(identifier)) is not None:
                embed = utilities.Embeds.package(message)
                await user.send(embed=embed)

    async def on_message(self, message: discord.Message) -> None:
        """Track each message and post mentioned messages to each person's inbox."""
        if message.guild is not None and message.guild.id == self.guild:
            if self.identifier_check(message):
                await self.post(message)

            elif message.reference is not None and message.reference.message_id is not None:
                resolved = await message.channel.fetch_message(message.reference.message_id)
                if self.identifier_check(resolved):
                    await self.post(resolved)

def setup(bot):
    cog = Magic(bot)
    bot.add_cog(cog)
