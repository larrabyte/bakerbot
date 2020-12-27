from discord.ext import commands
import utilities
import wavelink
import discord
import asyncio
import typing
import re

class player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = []
        self.cursor = 0

    async def advance(self):
        if len(self.queue) > self.cursor: await self.play(self.queue[self.cursor])
        else: raise utilities.NoTracksFound

    async def addtracks(self, ctx: commands.Context, tracks: typing.Union[wavelink.TrackPlaylist, wavelink.Track, list]):
        if isinstance(tracks, wavelink.TrackPlaylist): self.queue.extend(*tracks.tracks)
        elif isinstance(tracks, wavelink.Track): self.queue.append(tracks)
        elif isinstance(tracks, list): self.queue.extend(tracks)

    async def connect(self, ctx: commands.Context, requested: discord.VoiceChannel = None):
        if (channel := getattr(ctx.author.voice, "channel", requested)) == None and (channel := requested) == None: raise utilities.NoChannelToConnectTo
        if self.is_connected: raise utilities.AlreadyConnectedToChannel
        await super().connect(channel.id)
        return channel

    async def teardown(self):
        try: await self.destroy()
        except KeyError: pass

class voice(commands.Cog, wavelink.WavelinkMixin):
    """Bakerbot's voice client can be found here."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.startnodes())

    @commands.command()
    async def surpriseaudio(self, ctx: commands.Context, channel: discord.VoiceChannel, query: str):
        """Surprise someone in another channel with Bakerbot's presence (only accepts URLs)."""
        query = query.strip("<>")
        if re.match(utilities.urlRegex, query):
            player = await self.getplayer(ctx)
            results = await self.wavelink.get_tracks(query)
            if not results: raise utilities.NoTracksFound
            await player.addtracks(ctx, results)

            if ctx.author.voice: ctx.author.voice.channel = None
            await player.connect(ctx, channel)
            await player.advance()
        else:
            embed = discord.Embed(title="Bakerbot: Audio search failure.", colour=utilities.errorColour)
            embed.description = "The query must be a URL."
            await ctx.send(embed=embed)

    @commands.command()
    async def play(self, ctx: commands.Context, *, query: typing.Optional[str]):
        """Plays audio based on the query passed in. Can also resume playback if paused."""
        player = await self.getplayer(ctx)
        if not player.is_connected:
            await player.connect(ctx)
        elif not query and player.is_paused:
            await player.set_pause(False)
            return

        query = query.strip("<>")
        if re.match(utilities.urlRegex, query):
            results = await self.wavelink.get_tracks(query)
            if not results: raise utilities.NoTracksFound
            await player.addtracks(ctx, results)
        else:
            results = await self.wavelink.get_tracks(f"ytsearch:{query}")
            if not results: raise utilities.NoTracksFound
            await player.addtracks(ctx, results[0])

        if not player.is_playing: await player.advance()

    @commands.command()
    async def search(self, ctx: commands.Context, *, query: str):
        """Search for your favourite song here."""
        player = await self.getplayer(ctx)
        if not player.is_connected: await player.connect(ctx)

        results = await self.wavelink.get_tracks(f"ytsearch:{query}")
        if not results: raise utilities.NoTracksFound
        results = results[:5]

        embed = discord.Embed(title="Bakerbot: Audio search results.", colour=utilities.regularColour)
        listing = ""

        for index, track in enumerate(results):
            length = str(track.length // (1000 * 60)) + ":" + str((track.length // 1000) % 60).zfill(2)
            listing += f"**{index + 1}**. {track.title} ({length})\n"

        embed.description = listing
        embed.set_footer(text=f"Requested by {ctx.author.name}.", icon_url=ctx.author.avatar_url)
        message = await ctx.send(embed=embed)

        possibleReactions = list(utilities.reactionOptions.keys())[:min(len(results), len(utilities.reactionOptions))]
        for emojis in possibleReactions: await message.add_reaction(emojis)
        try: reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=lambda event, user: event.emoji in utilities.reactionOptions.keys() and user == ctx.author and event.message.id == message.id)
        except asyncio.TimeoutError: await ctx.message.delete()
        else: await player.addtracks(ctx, results[utilities.reactionOptions[reaction.emoji] - 1])

        await message.delete()
        if not player.is_playing: await player.advance()

    @commands.command()
    async def queue(self, ctx: commands.Context):
        """Gets the currently active music queue."""
        player = await self.getplayer(ctx)
        embed = discord.Embed(title="Bakerbot: Current audio queue.", colour=utilities.regularColour)
        embed.set_footer(text=f"Requested by {ctx.author.name}.", icon_url=ctx.author.avatar_url)

        if not player.queue or len(player.queue) <= player.cursor:
            embed.description = "The queue is currently empty."
        else:
            elapsed = str(int(player.position // (1000 * 60))) + ":" + str(int((player.position // 1000) % 60)).zfill(2)
            length = str(player.queue[player.cursor].length // (1000 * 60)) + ":" + str((player.queue[player.cursor].length // 1000) % 60).zfill(2)

            if history := player.queue[:player.cursor]:
                text = "\n".join(track.title for track in history)
                embed.add_field(name="Audio track history.", value=text, inline=False)

            embed.add_field(name=f"Currently playing: `[{elapsed} / {length}]`", value=player.queue[player.cursor].title, inline=False)

            if upcoming := player.queue[player.cursor + 1:]:
                text = "\n".join(track.title for track in upcoming)
                embed.add_field(name="Queued audio tracks.", value=text, inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx: commands.Context):
        """Skips to the next available audio track."""
        player = await self.getplayer(ctx)

        if upcoming := player.queue[player.cursor + 1:]:
            await player.stop()
        else:
            embed = discord.Embed(text="Bakerbot: Voice client status.", description="No audio tracks are currently queued.", colour=utilities.errorColour)
            await ctx.send(embed=embed)
            return

    @commands.command()
    async def rewind(self, ctx: commands.Context):
        """Rewinds to the previous audio track if available."""
        player = await self.getplayer(ctx)

        if history := player.queue[:player.cursor]:
            player.cursor -= 2
            await player.stop()
        else:
            embed = discord.Embed(text="Bakerbot: Voice client status.", description="No audio track history found.", colour=utilities.errorColour)
            await ctx.send(embed=embed)
            return

    @commands.command()
    async def pause(self, ctx: commands.Context):
        """Pause the Bakerbot if any audio is playing."""
        player = await self.getplayer(ctx)
        await player.set_pause(True)

    @commands.command()
    async def stop(self, ctx: commands.Context):
        """Stops the Bakerbot from playing audio and clears the active queue."""
        player = await self.getplayer(ctx)
        player.queue.clear()
        await player.stop()

    @commands.command()
    async def connect(self, ctx: commands.Context, *, channel: typing.Optional[discord.VoiceChannel]):
        """Joins the requester's voice channel or the specified channel."""
        player = await self.getplayer(ctx)
        if channel and ctx.author.voice: ctx.author.voice.channel = None
        channel = await player.connect(ctx, channel)
        embed = discord.Embed(title="Bakerbot: Voice client status.", description=f"Successfully connected to {channel.name}.", colour=utilities.successColour)
        await ctx.send(embed=embed)

    @commands.command()
    async def disconnect(self, ctx: commands.Context):
        """Disconnects from a voice channel if still connected."""
        player = await self.getplayer(ctx)
        await player.teardown()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Fired everytime Bakerbot is able to receive a VoiceState update."""
        if not member.bot and after.channel == None:
            if not [member for member in before.channel.members if not member.bot]:
                player = await self.getplayer(member.guild)
                if not player.is_paused: await player.set_pause(True)
        else:
            player = await self.getplayer(member.guild)
            if after.channel.id == player.channel_id:
                if player.is_paused: await player.set_pause(False)

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node: wavelink.Node):
        """Fired after each Wavelink node has been setup."""
        print(f"Wavelink node \"{node.identifier}\" ready.")

    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node: wavelink.Node, payload: typing.Union[wavelink.TrackEnd, wavelink.TrackStuck, wavelink.TrackException]):
        """Advances the queue cursor after every stop event."""
        payload.player.cursor += 1
        await payload.player.advance()

    async def startnodes(self):
        """Starts the Wavelink nodes."""
        await self.bot.wait_until_ready()
        for node in utilities.wavelinkNodes.values(): await self.wavelink.initiate_node(**node)

    async def getplayer(self, obj: typing.Union[discord.Guild, commands.Context]):
        """Retrieves the Wavelink player using either a guild or context."""
        if isinstance(obj, commands.Context): return self.wavelink.get_player(obj.guild.id, cls=player, context=obj)
        elif isinstance(obj, discord.Guild): return self.wavelink.get_player(obj.id, cls=player)

def setup(bot): bot.add_cog(voice(bot))
