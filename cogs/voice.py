import utilities
import model

from discord.ext import commands
import typing as t
import pathlib
import discord

class Voice(commands.Cog):
    """Houses Bakerbot's voice client: audio-related commands can be found here."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    def cog_unload(self) -> None:
        """Ensures clients are disconnected when this cog is unloaded."""
        for client in self.bot.voice_clients:
            coro = client.disconnect()
            self.bot.loop.create_task(coro)

    def paginate_tracks(self) -> utilities.Paginator:
        """Returns an instance of `utilities.Paginator` containing all music tracks."""
        paginator = utilities.Paginator()
        paginator.placeholder = "Tracks"

        for track in pathlib.Path("music").iterdir():
            label = utilities.Limits.limit(track.name, utilities.Limits.SELECT_LABEL)
            value = utilities.Limits.limit(track.name, utilities.Limits.SELECT_VALUE)
            desc = utilities.Limits.limit(str(track), utilities.Limits.SELECT_DESCRIPTION)
            option = discord.SelectOption(label=label, value=value, description=desc)
            paginator.add(option)

        return paginator

    async def cog_check(self, ctx: commands.Context) -> None:
        """Ensures that commands are being executed in a guild context."""
        return ctx.guild is not None

    async def connect(self, channel: discord.VoiceChannel) -> None:
        """Either connects or moves the bot to a specific voice channel."""
        client = channel.guild.voice_client
        if client is None or not client.is_connected():
            await channel.connect()
        elif client.channel != channel:
            await client.move_to(channel)

    @commands.group(invoke_without_subcommand=True)
    async def vc(self, ctx: commands.Context) -> None:
        """The parent command for Bakerbot's voice client."""
        summary = ("You've encountered Bakerbot's voice client! "
                   "See `$help voice` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @vc.command()
    async def play(self, ctx: commands.Context, track: t.Optional[str]) -> None:
        """Plays audio tracks from Bakerbot's music folder."""
        if track is None:
            paginator = self.paginate_tracks()
            await ctx.reply("Select any track to begin playing it.", view=paginator)
            if (track := await paginator.wait()) is None:
                return

        if not (filepath := pathlib.Path(f"music/{track}")).is_file():
            fail = utilities.Embeds.status(False)
            fail.description = f"`{track}` is not a valid track."

            trackcmd = f"{self.tracks.full_parent_name} {self.tracks.name}"
            trackcmd += self.tracks.signature or ""
            fail.set_footer(text=f"Consider invoking ${trackcmd} for a list of available tracks.", icon_url=utilities.Icons.INFO)
            return await ctx.reply(embed=fail)

        if ctx.author.voice is not None and ctx.author.voice.channel is not None:
            await self.connect(ctx.author.voice.channel)
        elif ctx.voice_client is None:
            fail = utilities.Embeds.status(False)
            fail.description = "What channel am I supposed to play audio in?"

            joincmd = f"{self.join.full_parent_name} {self.join.name}"
            joincmd += self.join.signature or ""
            fail.set_footer(text=f"Consider invoking ${joincmd} to make Bakerbot join a voice channel.", icon_url=utilities.Icons.INFO)
            return await ctx.reply(embed=fail)

        track = await discord.FFmpegOpusAudio.from_probe(filepath)
        embed = utilities.Embeds.standard()
        embed.set_footer(text=f"Interaction sent by {ctx.author}.", icon_url=utilities.Icons.INFO)
        embed.description = f"Now playing `{filepath}`."

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()

        ctx.voice_client.play(track)
        await ctx.reply(embed=embed)

    @vc.command(aliases=["list"])
    async def tracks(self, ctx: commands.Context) -> None:
        """Presents a list of Bakerbot's tracks."""
        paginator = self.paginate_tracks()
        await ctx.reply("These menus are only for viewing (selecting a track won't do anything).", view=paginator)

    @vc.command(aliases=["connect"])
    async def join(self, ctx: commands.Context, *, channel: t.Optional[discord.VoiceChannel]) -> None:
        """Joins the voice channel that the invoker is in, or `channel` if specified."""
        channel = channel or getattr(ctx.author.voice, "channel", None)

        if channel is None:
            fail = utilities.Embeds.status(False)
            fail.description = "No available channels exist (either none specified or you aren't in one)."
            return await ctx.reply(embed=fail)

        await self.connect(channel)

    @vc.command(aliases=["disconnect"])
    async def leave(self, ctx: commands.Context) -> None:
        """Disconnects the bot from any voice channels."""
        if ctx.voice_client is not None and ctx.voice_client.is_connected():
            await ctx.voice_client.disconnect()

def setup(bot: model.Bakerbot) -> None:
    cog = Voice(bot)
    bot.add_cog(cog)
