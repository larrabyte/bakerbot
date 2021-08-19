import discord.ext.commands as commands
import libs.utilities as utilities
import typing as t
import pathlib
import discord
import model

class Voice(commands.Cog):
    """Houses the voice client for Bakerbot. Audio commands can be found here."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    def cog_unload(self) -> None:
        """Ensures a clean disconnect from any voice clients on unload."""
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
        """The parent command for voice client management."""
        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                # There is no subcommand: inform the user about voice clients.
                summary = """Hi! Welcome to Bakerbot's voice client command group.
                            This cog houses commands related to audio.
                            See `$help voice` for a full list of available subcommands."""

                embed = discord.Embed(colour=utilities.Colours.regular, timestamp=discord.utils.utcnow())
                embed.description = summary
                embed.set_footer(text="Dunno what to put here.", icon_url=utilities.Icons.info)
                await ctx.reply(embed=embed)
            else:
                # The subcommand was not valid: throw a fit.
                command = f"${ctx.command.name} {ctx.subcommand_passed}"
                summary = f"`{command}` is not a valid command."
                footer = "Try $help voice for a full list of available subcommands."
                embed = utilities.Embeds.status(False, summary)
                embed.set_footer(text=footer, icon_url=utilities.Icons.cross)
                await ctx.reply(embed=embed)

    @vc.command()
    async def upload(self, ctx: commands.Context) -> None:
        """Uploads a file to Bakerbot's music repository."""
        embed = utilities.Embeds.status(True, None)
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
        """Plays audio tracks from the music folder."""
        if track is None:
            paginator = utilities.Paginator()
            paginator.placeholder = "Tracks"

            for track in pathlib.Path("music").iterdir():
                label = f"{track.name[0:22]}..." if len(track.name) > 25 else track.name
                option = discord.SelectOption(label=label, value=track.name, description=str(track))
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
        embed = discord.Embed(colour=utilities.Colours.regular, timestamp=discord.utils.utcnow())
        embed.set_footer(text="Interaction complete.", icon_url=utilities.Icons.info)
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
        """Disconnects the bot from any guild voice channels."""
        vc = ctx.guild.voice_client
        if vc is not None and vc.is_connected():
            await vc.disconnect()

def setup(bot: model.Bakerbot) -> None:
    cog = Voice(bot)
    bot.add_cog(cog)
