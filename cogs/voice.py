from discord.ext import commands
import utilities
import wavelink
import discord
import typing

class player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
    async def join(self, ctx: commands.Context, *, channel: typing.Optional[discord.VoiceChannel]):
        """Joins the requester's voice channel or the specified channel."""
        player = await self.getplayer(ctx)
        channel = await player.connect(ctx, channel)
        embed = discord.Embed(title="Bakerbot: Voice client status.", description=f"Successfully connected to {channel.name}.", colour=utilities.successColour)
        await ctx.send(embed=embed)

    @commands.command()
    async def leave(self, ctx: commands.Context):
        """Disconnects from a voice channel if still connected."""
        player = await self.getplayer(ctx)
        await player.teardown()

    async def startnodes(self):
        """Starts the Wavelink nodes."""
        await self.bot.wait_until_ready()
        for node in utilities.wavelinkNodes.values(): await self.wavelink.initiate_node(**node)

    async def getplayer(self, obj: typing.Union[discord.Guild, commands.Context]):
        """Retrieves the Wavelink player using either a guild or context."""
        if isinstance(obj, commands.Context): return self.wavelink.get_player(obj.guild.id, cls=player, context=obj)
        elif isinstance(obj, discord.Guild): return self.wavelink.get_player(obj.id, cls=player)

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

def setup(bot): bot.add_cog(voice(bot))
