import backend.utilities as utilities
import backend.discord as expcord
import model

import discord.ext.commands as commands
import typing as t
import asyncio
import discord
import random

class Magic(commands.Cog):
    """You can find dumb ideas from Team Magic here."""
    def __init__(self, bot: model.Bakerbot):
        self.magic = 473426067823263749
        self.sniper = MessageResender(bot, self.magic)
        self.disconnecter = Disconnecter(bot, self.magic)
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> None:
        return (await self.bot.is_owner(ctx.author)) or ctx.guild.id == self.magic

    @commands.group(invoke_without_subcommand=True)
    async def magic(self, ctx: commands.Context) -> None:
        """The parent command for all things Team Magic related."""
        summary = ("You've encountered Team Magic's command group!"
                    "See `$help magic` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @magic.command()
    async def nodelete(self, ctx: commands.Context) -> None:
        """Enables/disables the `on_message_delete()` listener for Team Magic."""
        self.sniper.enabled = not self.sniper.enabled
        await ctx.reply(f"`on_message_delete()` listener is (now?) set to: `{self.sniper.enabled}`")

    @magic.command()
    async def demux(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str) -> None:
        """A demultiplexing experiment using Discord webhooks."""
        endpoints = await channel.webhooks()
        user, avatar = ctx.author.display_name, self.bot.user.avatar.url
        tasks = [hook.send(message, username=user, avatar_url=avatar) for hook in endpoints]
        await asyncio.gather(*tasks)

    @magic.command()
    async def hookify(self, ctx: commands.Context, source: discord.TextChannel, destination: t.Optional[discord.TextChannel]) -> None:
        """So it turns out you can have more than 10 webooks in a channel..."""
        hooks = await source.webhooks()

        if destination is None:
            webhooks = "\n".join(str(w.id) for w in hooks)
            return await ctx.reply(webhooks)

        for i in range(10 - len(hooks)):
            rand = random.randint(0, 2**32)
            name = f"bakerbot hook #{rand}"
            await expcord.Webhooks.create(self.bot, source, name)

        # Refresh the list of hooks after we create more.
        for webhook in (await source.webhooks()):
            await expcord.Webhooks.move(self.bot, webhook, destination)

        await ctx.reply("Webhooks created and moved.")

    @magic.command()
    async def gandalf(self, ctx: commands.Context, member: discord.Member) -> None:
        """Prevents a member from joining a voice channel."""
        mentions = discord.AllowedMentions.none()

        if member.id in self.disconnecter.targets:
            self.disconnecter.targets.remove(member.id)
            await ctx.reply(f"{member.mention} shall pass!", allowed_mentions=mentions)
        else:
            self.disconnecter.targets.add(member.id)
            if member.voice is not None and member.voice.channel is not None:
                await member.move_to(None)

            await ctx.reply(f"{member.mention} shall not pass!", allowed_mentions=mentions)

class MessageResender:
    """A wrapper around `on_message_delete()` for Team Magic."""
    def __init__(self, bot: model.Bakerbot, guild: int) -> None:
        self.ignore = set()
        self.guild = guild
        self.enabled = False

        bot.loop.create_task(self.initialise(bot))
        bot.add_listener(self.on_message_delete)

    async def initialise(self, bot: model.Bakerbot) -> None:
        """Initialises a `MessageResender` instance."""
        if bot.user is None:
            await bot.wait_until_ready()

        self.ignore.add(bot.user.id)

    async def on_message_delete(self, message: discord.Message) -> None:
        """Team Magic-specific listener for resending deleted messages."""
        if self.enabled and message.author.id not in self.ignore and message.guild.id == self.guild:
            embed = discord.Embed(colour=utilities.Colours.REGULAR, timestamp=message.created_at)
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.set_footer(text="NUTS!", icon_url=utilities.Icons.INFO)
            embed.description = message.content
            await message.channel.send(embed=embed)

class Disconnecter:
    """A wrapper around `on_voice_state_update()` for Team Magic."""
    def __init__(self, bot: model.Bakerbot, guild: int) -> None:
        self.guild = guild
        self.targets = set()
        bot.add_listener(self.on_voice_state_update)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        """Team Magic-specific listener for preventing members from joining voice channels."""
        if member.id in self.targets and after.channel is not None:
            await member.move_to(None)

def setup(bot):
    cog = Magic(bot)
    bot.add_cog(cog)
