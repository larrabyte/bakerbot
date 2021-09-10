import utilities
import model

import discord.ext.commands as commands
import typing as t
import pathlib
import discord

class Voice(commands.Cog):
    """Houses Bakerbot's voice client: audio-related commands can be found here."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    def cog_unload(self) -> None:
        for client in self.bot.voice_clients:
            coro = self.cog_unload_disconnect(client)
            self.bot.loop.create_task(coro)

    async def cog_unload_disconnect(self, client: discord.VoiceClient) -> None:
        """Asynchronous unloading task for disconnecting voice clients."""
        await client.disconnect()

    async def connect(self, channel: discord.VoiceChannel) -> None:
        """Either connects or moves the bot to a specific voice channel."""
        client = channel.guild.voice_client
        offline = client is None or not client.is_connected()
        function = channel.connect() if offline else client.move_to(channel)
        await function

    async def ensure_client(self, remote: t.Optional[discord.VoiceClient]) -> bool:
        """Returns the state of the voice client after attempting a connection."""
        if remote is None or remote.channel is None:
            return False

        await self.connect(remote.channel)
        return True

    @commands.group(invoke_without_subcommand=True)
    async def vc(self, ctx: commands.Context) -> None:
        """The parent command for Bakerbot's voice client."""
        summary = ("You've encountered Bakerbot's voice client! "
                   "See `$help voice` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @vc.command()
    async def upload(self, ctx: commands.Context) -> None:
        """Uploads a file to Bakerbot's music repository."""
        embed = utilities.Embeds.status(True, "")
        saved = 0

        async with ctx.typing():
            for attachment in ctx.message.attachments:
                filepath = f"music/{attachment.filename}"
                if pathlib.Path(filepath).is_file():
                    await attachment.save(filepath)
                    saved += 1

        embed.description = f"Uploaded {saved} files!"
        await ctx.reply(embed=embed)

    @vc.command()
    async def play(self, ctx: commands.Context, track: t.Optional[str]) -> None:
        """Plays audio tracks from Bakerbot's music folder."""
        if track is None:
            paginator = utilities.Paginator()
            paginator.placeholder = "Tracks"

            for track in pathlib.Path("music").iterdir():
                label = utilities.Limits.limit(track.name, utilities.Limits.SELECT_LABEL)
                value = utilities.Limits.limit(track.name, utilities.Limits.SELECT_VALUE)
                desc = utilities.Limits.limit(str(track), utilities.Limits.SELECT_DESCRIPTION)
                option = discord.SelectOption(label=label, value=value, description=desc)
                paginator.add(option)

            await ctx.reply("Please select a track from the dropdown menu.", view=paginator)
            track = await paginator.wait()
            if track is None:
                return

        filepath = pathlib.Path(f"music/{track}")
        if not filepath.is_file():
            fail = utilities.Embeds.status(False, f"{track} is not a valid track.")
            return await ctx.reply(embed=fail)

        if not (await self.ensure_client(ctx.author.voice)):
            fail = utilities.Embeds.status(False, "Unable to join a channel.")
            return await ctx.reply(embed=fail)

        track = await discord.FFmpegOpusAudio.from_probe(filepath)
        embed = utilities.Embeds.standard()
        embed.set_footer(text="Interaction complete.", icon_url=utilities.Icons.INFO)
        embed.description = f"Now playing `{filepath}`."

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()

        ctx.voice_client.play(track)
        await ctx.reply(embed=embed)

    @vc.command()
    async def join(self, ctx: commands.Context, *, channel: t.Optional[discord.VoiceChannel]) -> None:
        """Joins the voice channel that the invoker is in, or `channel` if specified."""
        channel = channel or getattr(ctx.author.voice, "channel", None)

        if channel is None:
            response = "No available channels exist (either none specified or you aren't in one)."
            fail = utilities.Embeds.status(False, response)
            return await ctx.reply(embed=fail)

        await self.connect(channel)

    @vc.command()
    async def leave(self, ctx: commands.Context) -> None:
        """Disconnects the bot from any voice channels."""
        vc = ctx.guild.voice_client
        if vc is not None and vc.is_connected():
            await vc.disconnect()

def setup(bot: model.Bakerbot) -> None:
    cog = Voice(bot)
    bot.add_cog(cog)
