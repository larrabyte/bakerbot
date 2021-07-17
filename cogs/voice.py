import discord.ext.commands as commands
import typing as t
import pathlib
import discord
import model

class Voice(commands.Cog):
    """Houses the voice client for Bakerbot. Audio commands can be found here."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.colours = bot.utils.Colours
        self.icons = bot.utils.Icons
        self.embeds = bot.utils.Embeds
        self.bot = bot

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
                # There is no subcommand: inform the user about the module manager.
                summary = """Hi! Welcome to Bakerbot's voice client command group.
                            This cog houses commands related to audio.
                            See `$help voice` for a full list of available subcommands."""

                embed = discord.Embed(colour=self.colours.regular, timestamp=self.embeds.now())
                embed.description = summary
                embed.set_footer(text="Dunno what to put here.", icon_url=self.icons.info)
                await ctx.reply(embed=embed)
            else:
                # The subcommand was not valid: throw a fit.
                command = f"${ctx.command.name} {ctx.subcommand_passed}"
                summary = f"`{command}` is not a valid command."
                footer = "Try $help voice for a full list of available subcommands."
                embed = self.embeds.status(False, summary)
                embed.set_footer(text=footer, icon_url=self.icons.cross)
                await ctx.reply(embed=embed)

    @vc.command()
    async def play(self, ctx: commands.Context, track: t.Optional[str]) -> None:
        """Plays audio tracks from the music folder."""
        if track is None:
            view = SelectionView.create(self)
            content = "Please select a track from the dropdown menu."
            return await ctx.reply(content, view=view)

        filepath = pathlib.Path(f"music/{track}")
        if not filepath.is_file():
            fail = self.embeds.status(False, f"`{track}` does not exist.")
            return await ctx.reply(embed=fail)

        if not (await self.ensure_client(ctx.author.voice)):
            fail = self.embeds.status(False, "Unable to join a channel.")
            return await ctx.reply(embed=fail)

        track = await discord.FFmpegOpusAudio.from_probe(str(filepath))
        embed = discord.Embed(colour=self.colours.regular, timestamp=self.embeds.now())
        embed.set_footer(text="Interaction complete.", icon_url=self.icons.info)
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
            fail = self.embeds.status(False, response)
            return await ctx.reply(embed=fail)

        await self.connect(channel)

    @vc.command()
    async def leave(self, ctx: commands.Context) -> None:
        """Disconnects the bot from any guild voice channels."""
        vc = ctx.guild.voice_client
        if vc is not None and vc.is_connected():
            await vc.disconnect()

class SelectionView(discord.ui.View):
    """A discord.ui.View subclass for audio selection."""
    @classmethod
    def create(cls, cog: Voice) -> "SelectionView":
        """Creates and returns an instance of `SelectionView`."""
        instance = SelectionView()
        instance.colours = cog.bot.utils.Colours
        instance.embeds = cog.bot.utils.Embeds
        instance.icons = cog.bot.utils.Icons
        instance.cog = cog

        # Setup the selection menu.
        menu = discord.ui.Select(placeholder="Click me!")
        folder = pathlib.Path("music")

        for files in folder.iterdir():
            path = str(files)
            menu.add_option(label=path[:25], value=path)

        menu.callback = instance.menu_callback
        instance.add_item(menu)
        return instance

    async def menu_callback(self, interaction: discord.Interaction) -> None:
        """Handles menu interactions."""
        if not (await self.cog.ensure_client(interaction.user.voice)):
            fail = self.embeds.status(False, "Unable to join a channel.")
            return await interaction.response.edit_message(content=None, embed=fail, view=None)

        choice = self.children[0].values[0]
        track = await discord.FFmpegOpusAudio.from_probe(choice)

        client = interaction.guild.voice_client
        embed = discord.Embed(colour=self.colours.regular, timestamp=self.embeds.now())
        embed.set_footer(text="Interaction complete.", icon_url=self.icons.info)
        embed.description = f"Now playing `{choice}`."

        if client.is_playing() or client.is_paused():
            client.stop()

        await interaction.response.edit_message(content=None, embed=embed, view=None)
        client.play(track)

def setup(bot: model.Bakerbot) -> None:
    cog = Voice(bot)
    bot.add_cog(cog)
