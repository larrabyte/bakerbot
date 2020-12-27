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
        if (self.queue and self.cursor == 0) or (len(self.queue) - 1 >= self.cursor + 1):
            await self.play(self.queue[self.cursor])
            self.cursor += 1

    async def addtracks(self, ctx: commands.Context, tracks: typing.Union[wavelink.TrackPlaylist, wavelink.Track, list]):
        if isinstance(tracks, wavelink.TrackPlaylist): self.queue.extend(*tracks.tracks)
        elif isinstance(tracks, wavelink.Track): self.queue.append(tracks)
        elif isinstance(tracks, list): self.queue.extend(tracks)

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
        """Plays audio based on the query passed in. Delegates to $search if required."""
        player = await self.getplayer(ctx)
        if not player.is_connected: await player.connect(ctx)

        query = query.strip("<>")
        if re.match(utilities.urlRegex, query):
            results = await self.wavelink.get_tracks(query)
            if not results: raise utilities.NoTracksFound
            await player.addtracks(ctx, results)
        else: await ctx.invoke(self.search, query=query)
        if not player.is_playing: await player.advance()

    @commands.command()
    async def search(self, ctx: commands.Context, *, query: str):
        """Search for your favourite song here."""
        player = await self.getplayer(ctx)
        if not player.is_connected: await player.connect(ctx)

        results = list(await self.wavelink.get_tracks(f"ytsearch:{query}"))[:5]
        if not results: raise utilities.NoTracksFound
        embed = discord.Embed(title="Bakerbot: Audio search results.", colour=utilities.regularColour)
        listing = ""

        for index, track in enumerate(results):
            title = (track.title + "...") if len(track.title) > (50 + 3) else track.title
            length = str(track.length // (1000 * 60)) + ":" + str((track.length // 1000) % 60).zfill(2)
            listing += f"**{index + 1}**. {title} ({length})\n"

        embed.description = listing
        embed.set_footer(text=f"Invoked by {ctx.author.name}.", icon_url=ctx.author.avatar_url)
        message = await ctx.send(embed=embed)

        possibleReactions = list(utilities.reactionOptions.keys())[:min(len(results), len(utilities.reactionOptions))]
        for emojis in possibleReactions: await message.add_reaction(emojis)
        try: reaction, user = await self.bot.wait_for("reaction_add", timeout=60, check=lambda event, user: event.emoji in utilities.reactionOptions.keys() and user == ctx.author and event.message.id == message.id)
        except asyncio.TimeoutError: await ctx.message.delete()
        else: await player.addtracks(ctx, results[utilities.reactionOptions[reaction.emoji]])

        await message.delete()
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
