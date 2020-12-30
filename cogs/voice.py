from discord.ext import commands
import datetime as dt
import typing as t
import wavelink
import discord
import asyncio
import re

class VoiceError(commands.CommandError):
    QUEUE_EMPTY             = (0, "Queue is currently empty.")
    ALREADY_CONNECTED       = (1, "Already connected to a voice channel.")
    NO_CHANNEL              = (2, "No channel to connect to.")
    INVALID_REPEAT_MODE     = (3, "Invalid repeat mode.")
    NO_UPCOMING_TRACKS      = (4, "No upcoming tracks to skip to.")
    NO_PREVIOUS_TRACKS      = (5, "No previous tracks to rewind to.")
    NO_TRACKS_FOUND         = (6, "No tracks found.")
    ASYNCIO_TIMEOUT         = (7, "Search timed out.")

    def __init__(self, error: tuple) -> None: self.error = error
    def __str__(self) -> str: return f"VoiceError({self.error[0]}) raised: {self.error[1]}"

class Queue:
    def __init__(self) -> None:
        self.internal = []
        self.repeat_mode = 0
        self.index = 0

    @property
    def length(self) -> int:
        return len(self.internal)

    @property
    def is_empty(self) -> bool:
        return not self.internal

    @property
    def current_track(self) -> wavelink.Track:
        if self.is_empty: raise VoiceError(VoiceError.QUEUE_EMPTY)
        elif self.index < len(self.internal): return self.internal[self.index]
        return None

    @property
    def upcoming(self) -> list:
        if self.is_empty: raise VoiceError(VoiceError.QUEUE_EMPTY)
        return self.internal[self.index + 1:]

    @property
    def history(self) -> list:
        if self.is_empty: raise VoiceError(VoiceError.QUEUE_EMPTY)
        return self.internal[:self.index]

    def get_next_track(self) -> t.Optional[wavelink.Track]:
        if self.is_empty: raise VoiceError(VoiceError.QUEUE_EMPTY)

        self.index += 1
        if self.index < 0: return None
        elif self.index > len(self.internal) - 1:
            if self.repeat_mode == 2: self.index = 0
            else: return None

        return self.internal[self.index]

    def clear_queue(self) -> None:
        self.internal.clear()
        self.index = 0

class Player(wavelink.Player):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.queue = Queue()

    async def playback(self) -> None:
        await self.play(self.queue.current_track)

    async def advance(self) -> None:
        next_track = self.queue.get_next_track()
        if next_track is None: await self.stop()
        else: await self.play(next_track)

    async def add_tracks(self, ctx: commands.Context, tracks: t.Union[list, wavelink.Track]) -> None:
        if isinstance(tracks, wavelink.Track): self.queue.internal.append(tracks)
        elif isinstance(tracks, list): self.queue.internal.extend(tracks.tracks)
        if not self.is_playing and not self.queue.is_empty: await self.playback()

    async def connect(self, ctx: commands.Context, channel: discord.VoiceChannel=None) -> discord.VoiceChannel:
        if self.is_connected: raise VoiceError(VoiceError.ALREADY_CONNECTED)
        candidate = getattr(ctx.author.voice, "channel", channel)
        if candidate is None: raise VoiceError(VoiceError.NO_CHANNEL)

        await super().connect(candidate.id)
        return candidate

    async def teardown(self) -> None:
        try: await self.destroy()
        except KeyError: pass

class Voice(commands.Cog, wavelink.WavelinkMixin, name="voice"):
    """Bakerbot's voice client can be found here!"""
    def __init__(self, bot: commands.Bot) -> None:
        self.wavelink = wavelink.Client(bot=bot)
        bot.loop.create_task(self.startup())
        self.bot = bot

    async def startup(self) -> None:
        """Manages any cog prerequisites."""
        await self.bot.wait_until_ready()
        self.util = self.bot.get_cog("utilities")

        for node in self.util.wavelink_nodes.values():
            await self.wavelink.initiate_node(**node)

    async def cog_check(self, ctx: commands.Context) -> None:
        """Run before any command is invoked. Listeners are exempt."""
        self.player = self.get_player(ctx)
        return True

    async def get_tracks(self, query: str, search: bool) -> list:
        """A helper function to get tracks from Wavelink."""
        query = f"ytsearch:{query}" if search else query
        results = await self.wavelink.get_tracks(query)
        if results is None: raise VoiceError(VoiceError.NO_TRACKS_FOUND)
        return list(results)

    def get_player(self, obj: t.Union[commands.Context, discord.Guild]) -> Player:
        """Returns the Guild's Player instance."""
        if isinstance(obj, commands.Context): return self.wavelink.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild): return self.wavelink.get_player(obj.id, cls=Player)

    def voice_embed(self, ctx: commands.Context, title: str, description: str) -> discord.Embed:
        """Returns a Discord Embed useful for voice information."""
        embed = discord.Embed(title=title, colour=self.util.regular_colour, timestamp=dt.datetime.utcnow())
        if description is not None: embed.description = description
        embed.set_footer(text=f"Requested by {ctx.author.name}.", icon_url=ctx.author.avatar_url)
        return embed

    def status_embed(self, ctx: commands.Context, title: str, description: str, success: bool) -> discord.Embed:
        """Returns a Discord Embed useful for displaying statuses."""
        colour = self.util.success_colour if success else self.util.error_colour
        icon = self.util.tick_icon if success else self.util.cross_icon
        embed = discord.Embed(title=title, description=description, colour=colour, timestamp=dt.datetime.utcnow())
        embed.set_footer(text=f"Requested by {ctx.author.name}.", icon_url=icon)
        return embed

    def track_embed(self, title: str, ctx: commands.Context, track: wavelink.Track) -> discord.Embed:
        """Returns a Discord Embed useful for displaying track information."""
        embed = self.voice_embed(ctx=ctx, title=title, description=f"[{track.title}]({track.uri})")
        if track.thumb is not None: embed.set_thumbnail(url=track.thumb)
        return embed

    @commands.command()
    async def play(self, ctx: commands.Context, *, query: t.Optional[str]) -> None:
        """Play some tunes! Also works as the resume command."""
        if not self.player.is_connected: await self.player.connect(ctx)
        elif query is None: await self.player.set_pause(False)

        query = query.strip("<>")
        search = True if re.match(self.util.url_regex, query) is None else False
        result = await self.get_tracks(query, search)

        title = "Bakerbot: Now playing." if not self.player.is_playing else "Bakerbot: Now queued."
        embed = self.track_embed(ctx=ctx, title=title, track=result[0])
        await ctx.send(embed=embed)
        await self.player.add_tracks(ctx, result[0])

    @commands.command()
    async def search(self, ctx: commands.Context, *, query: str) -> None:
        """Search for your favourite tunes!"""
        if not self.player.is_connected: await self.player.connect(ctx)

        results = await self.get_tracks(query, True)
        results = results[:5]
        list_text = ""

        for index, track in enumerate(results):
            length = f"{track.length // (1000 * 60)}:{str((track.length // 1000) % 60).zfill(2)}"
            list_text += f"**{index + 1}**. [{track.title}]({track.uri}) ({length})\n"

        check = lambda e, u: e.emoji in reactions and u == ctx.author and e.message.id == msg.id
        reactions = list(self.util.react_options.keys())[:min(len(results), len(self.util.react_options))]
        embed = self.voice_embed(ctx=ctx, title="Bakerbot: Audio search results.", description=list_text)

        msg = await ctx.send(embed=embed)
        for emoji in reactions:
            await msg.add_reaction(emoji)

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30, check=check)
            selection = results[self.util.react_options[reaction.emoji] - 1]
        except asyncio.TimeoutError:
            await msg.delete()
            raise VoiceError(VoiceError.ASYNCIO_TIMEOUT)

        await msg.delete()
        title = "Bakerbot: Now playing." if not self.player.is_playing else "Bakerbot: Now queued."
        embed = self.track_embed(ctx=ctx, title=title, track=selection)
        await ctx.send(embed=embed)
        await self.player.add_tracks(ctx, selection)

    @commands.command()
    async def queue(self, ctx: commands.Context) -> None:
        """Check out the current audio queue."""
        if self.player.queue.is_empty: raise VoiceError(VoiceError.QUEUE_EMPTY)
        embed = self.voice_embed(ctx=ctx, title="Bakerbot: Current audio queue.", description=None)

        h_text = ""
        if self.player.queue.history:
            for index, track in enumerate(self.player.queue.history):
                h_text += f"**{index + 1}**. [{track.title}]({track.uri})\n"

            embed.add_field(name="Audio track history.", value=h_text, inline=False)
        
        if (cur := self.player.queue.current_track) is not None:
            elapsed = f"{int(self.player.position) // (1000 * 60)}:{str((int(self.player.position) // 1000) % 60).zfill(2)}"
            length = f"{cur.length // (1000 * 60)}:{str((cur.length // 1000) % 60).zfill(2)}"
            name = f"Currently streaming: `[{elapsed}]`" if cur.is_stream else f"Currently playing: `[{elapsed} / {length}]`"
            embed.add_field(name=name, value=f"[{cur.title}]({cur.uri})", inline=False)
            if cur.thumb is not None: embed.set_thumbnail(url=cur.thumb)

        u_text = ""
        if self.player.queue.upcoming:
            for index, track in enumerate(self.player.queue.upcoming):
                u_text += f"**{index + 1}**. [{track.title}]({track.uri})\n"

            embed.add_field(name="Queued audio tracks.", value=u_text, inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def repeat(self, ctx: commands.Context, mode: t.Optional[str]) -> None:
        """Change the current repeat mode. Valid options include `none`, `one` and `all`."""
        if mode == "none": self.player.queue.repeat_mode = 0
        elif mode == "one": self.player.queue.repeat_mode = 1
        elif mode == "all": self.player.queue.repeat_mode = 2
        else: raise VoiceError(VoiceError.INVALID_REPEAT_MODE)

        embed = self.status_embed(title="Bakerbot: Queue repeat mode.",
                                  description=f"Successfully changed the repeat mode to `{mode}`.",
                                  success=True,
                                  ctx=ctx)

        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx: commands.Context) -> None:
        """Skips the current audio track."""
        if self.player.queue.repeat_mode != 1:
            if self.player.queue.upcoming: track = self.player.queue.upcoming[0]
            else: raise VoiceError(VoiceError.NO_UPCOMING_TRACKS)
        else: track = self.player.queue.current_track

        embed = self.track_embed(ctx=ctx, title="Bakerbot: Skipping to next track.", track=track)
        await ctx.send(embed=embed)

        if self.player.is_playing: await self.player.stop()
        else: await self.player.advance()

    @commands.command()
    async def rewind(self, ctx: commands.Context) -> None:
        """Rewinds to the previous audio track."""
        if self.player.queue.repeat_mode != 1:
            if self.player.queue.history:
                track = self.player.queue.history[-1]
                self.player.queue.index -= 2
            else: raise VoiceError(VoiceError.NO_PREVIOUS_TRACKS)
        else: track = self.player.queue.current_track

        embed = self.track_embed(ctx=ctx, title="Bakerbot: Rewinding to previous track.", track=track)
        await ctx.send(embed=embed)

        if self.player.is_playing: await self.player.stop()
        else: await self.player.advance()

    @commands.command()
    async def pause(self, ctx: commands.Context) -> None:
        """Pauses the voice client if any audio is currently playing."""
        if not self.player.is_paused:
            await self.player.set_pause(True)
            embed = self.status_embed(title="Bakerbot: Voice client status.",
                                      description="Audio successfully paused!",
                                      success=True,
                                      ctx=ctx)

            await ctx.send(embed=embed)

    @commands.command()
    async def stop(self, ctx: commands.Context) -> None:
        """Stops playback and clears the audio queue."""
        if not self.player.queue.is_empty:
            self.player.queue.clear_queue()
            await self.player.stop()
            embed = self.status_embed(title="Bakerbot: Queue status.",
                                      description="Queue successfully cleared!",
                                      success=True,
                                      ctx=ctx)

            await ctx.send(embed=embed)

    @commands.command()
    async def connect(self, ctx: commands.Context, *, channel: t.Optional[discord.VoiceChannel]) -> None:
        """Connects to the requester's voice channel, or a channel of their choice."""
        channel = await self.player.connect(ctx, channel)
        embed = self.status_embed(title="Bakerbot: Voice client status.",
                                    description=f"Successfully connected to {channel.name}.",
                                    success=True,
                                    ctx=ctx)

        await ctx.send(embed=embed)

    @commands.command()
    async def disconnect(self, ctx: commands.Context) -> None:
        """Disconnect the voice client from any voice channels."""
        if self.player.is_connected:
            await self.player.teardown()
            embed = self.status_embed(title="Bakerbot: Voice client status.",
                                      description="Successfully disconnected.",
                                      success=True,
                                      ctx=ctx)

            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Called when someone leaves or joins the voice channel."""
        if not member.bot and after.channel is None:
            if not [member for member in before.channel.members if not member.bot]:
                player = self.get_player(member.guild)
                if not player.is_paused: await player.set_pause(True)
        else:
            player = self.get_player(member.guild)
            if after.channel is not None and after.channel.id == player.channel_id:
                if player.is_paused: await player.set_pause(False)

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node: wavelink.Node) -> None:
        """Called when a Wavelink node is ready for use."""
        print(f"Wavelink node {node.identifier} ready.")

    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node: wavelink.Node, payload: object):
        """Called when the player stops playing audio."""
        if payload.player.queue.repeat_mode == 1: await payload.player.playback()
        else: await payload.player.advance()

def setup(bot): bot.add_cog(Voice(bot))
