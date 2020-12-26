from discord.ext import commands
import utilities
import wavelink
import discord
import typing
import re

class queue:
    def __init__(self):
        self.internal = []
        self.cursor = 0

    def add(self, *args):
        self.internal.extend(*args)

    @property
    def nextTrack(self):
        if not self.internal:
            raise utilities.QueueIsEmpty
        elif self.cursor == 0:
            self.cursor = 1
            return self.internal[0]
        elif self.cursor + 1 > len(self.internal) - 1: 
            return None

        self.cursor += 1
        return self.internal[self.cursor]

class player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue()

    async def advance(self):
        track = self.queue.nextTrack
        if track != None: await self.play(track)

    async def addtracks(self, ctx: commands.Context, tracks: typing.Union[wavelink.TrackPlaylist, list, None]):
        if not tracks: raise utilities.NoTracksFound
        if isinstance(tracks, wavelink.TrackPlaylist): self.queue.add(*tracks.tracks)
        elif isinstance(tracks, list): self.queue.add(tracks)
        else: pass

    async def connect(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        if (channel := getattr(ctx.author.voice, "channel", channel)) == None: raise utilities.NoChannelToConnectTo
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
    async def play(self, ctx: commands.Context, *, query: str):
        """Plays audio based on the query passed in."""
        player = await self.getplayer(ctx)
        if not player.is_connected: await player.connect(ctx)

        query = query.strip("<>")
        if not re.match(utilities.urlRegex, query): query = f"ytsearch:{query}"
        await player.addtracks(ctx, await self.wavelink.get_tracks(query))
        if not player.is_playing: await player.advance()

    @commands.command()
    async def connect(self, ctx: commands.Context, *, channel: typing.Optional[discord.VoiceChannel]):
        """Joins the requester's voice channel or the specified channel."""
        player = await self.getplayer(ctx)
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
                # TODO: Make the player pause the music rather than disconnect.
                player = await self.getplayer(member.guild)
                await player.teardown()

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node: wavelink.Node):
        """Fired after each Wavelink node has been setup."""
        print(f"Wavelink node \"{node.identifier}\" ready.")

    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node: wavelink.Node, payload: typing.Union[wavelink.TrackEnd, wavelink.TrackStuck, wavelink.TrackException]):
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
