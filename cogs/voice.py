from discord.ext import commands
import utilities
import wavelink
import discord
import typing

class player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class voice(commands.Cog, wavelink.WavelinkMixin):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.startnodes())

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
                pass  # Disconnect the bot from the channel.

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node: wavelink.Node):
        """Fired after each Wavelink node has been setup."""
        print(f"Wavelink node \"{node.identifier}\" ready.")

def setup(bot): bot.add_cog(voice(bot))
