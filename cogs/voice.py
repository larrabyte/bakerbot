from discord.ext import commands
from utilities import *
import discord
import os

class voice(commands.Cog):
    """Implements voice capabilities."""

    def __init__(self, bot):
        self.queue = []
        self.bot = bot

    async def unifiedplay(self, user: discord.Member, filepath: str=None):
        client = user.guild.voice_client
        if client == None or not client.is_connected(): await user.voice.channel.connect()
        elif client.channel != user.voice.channel: await client.move_to(user.voice.channel)
        if client.is_playing(): client.stop()

        if filepath:
            audio = await discord.FFmpegOpusAudio.from_probe(filepath)
            client.play(audio)

    @commands.command()
    async def join(self, ctx):
        """Make Bakerbot join your voice channel."""
        await self.unifiedplay(ctx.author)

    @commands.command(aliases=["dc"])
    async def disconnect(self, ctx):
        """Disconnects Bakerbot from the voice channel."""
        await ctx.guild.voice_client.disconnect()

    @commands.command()
    async def play(self, ctx, music: str=None):
        """Plays a local audio file or YouTube video.
           Optionally, accepts uploaded attachments."""
        pass

    @commands.command()
    async def pause(self, ctx):
        """Pause any playing music."""
        ctx.guild.voice_client.pause()

    @commands.command()
    async def resume(self, ctx):
        """Resume any music that is paused."""
        ctx.guild.voice_client.resume()

def setup(bot): bot.add_cog(voice(bot))
