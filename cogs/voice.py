from discord.ext import commands
from utilities import *
import youtube_dl
import validators
import discord
import os

ytformatopt = {
    "format": 'bestaudio/best',
    "outtmpl": '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0"
}

ffmpegopt = {
    "options": "-vn"
}

class voice(commands.Cog):
    """Implements voice capabilities."""

    def __init__(self, bot):
        self.ytdl = youtube_dl.YoutubeDL(ytformatopt)
        self.mfold = "data/music/"
        self.bot = bot

    async def getstream(self, query: str):
        if not validators.url(query): query = f"ytsearch1:{query}"
        data = await self.bot.loop.run_in_executor(None, lambda: self.ytdl.extract_info(query, download=False))
        if "entries" in data: data = data["entries"][0]
        audio = await discord.FFmpegOpusAudio.from_probe(data["url"], options=ffmpegopt)
        return (audio, data)

    @commands.command()
    async def stop(self, ctx):
        """Stop any audio from playing."""
        if ctx.voice_client: ctx.voice_client.stop()
        await ctx.send("Music stopped!", delete_after=5)

    @commands.command(aliases=["resume"])
    async def pause(self, ctx):
        """Pause/resume."""
        if ctx.voice_client:
            if ctx.voice_client.is_playing():
                ctx.voice_client.pause()
                await ctx.send("Audio paused :(", delete_after=10)
            elif ctx.voice_client.is_paused():
                ctx.voice_client.resume()
                await ctx.send("Audio resumed :)", delete_after=10)

    @commands.command()
    async def play(self, ctx, *, query: str):
        """Plays audio to a voice channel. Accepts both local filenames or YouTube URLs."""
        embed = getembed("Bakerbot: Now playing.", 0x9D00C4, "jingle jam 2020")

        if os.path.exists(self.mfold + query):
            audio = await discord.FFmpegOpusAudio.from_probe(self.mfold + query)
            embed.add_field(name="Local audio file.", value=query)
        else:
            audio, metadata = await self.getstream(query)
            embed.add_field(name="Remote audio source.", value=f"[{metadata['title']}]({metadata['webpage_url']})")

        if ctx.voice_client.is_playing(): ctx.voice_client.stop()
        ctx.voice_client.play(audio)
        await ctx.send(embed=embed)

    @commands.command()
    async def join(self, ctx):
        """Joins a voice channel."""
        if ctx.voice_client is not None: 
            if ctx.author.voice: await ctx.voice_client.move_to(ctx.author.voice.channel)
            else: await ctx.send("You are not connected to a voice channel.", delete_after=10)
        elif ctx.author.voice: await ctx.author.voice.channel.connect()
        else: await ctx.send("You are not connected to a voice channel.", delete_after=10)

    @commands.command(aliases=["dc"])
    async def disconnect(self, ctx):
        """Disconnects Bakerbot from any voice channels."""
        if ctx.voice_client: await ctx.voice_client.disconnect()
        await ctx.send("Voice client disconnected.", delete_after=10)

    @play.before_invoke
    async def ensureconnection(self, ctx):
        await self.join(ctx)

def setup(bot): bot.add_cog(voice(bot))
