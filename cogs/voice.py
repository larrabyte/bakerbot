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

    @commands.command()
    async def stop(self, ctx):
        """Stop any audio from playing."""
        if ctx.voice_client: ctx.voice_client.stop()

    @commands.command(aliases=["resume"])
    async def pause(self, ctx):
        """Pause/resume."""
        if ctx.voice_client:
            if ctx.voice_client.is_playing(): ctx.voice_client.pause()
            elif ctx.voice_client.is_paused(): ctx.voice_client.resume()

    @commands.command()
    async def play(self, ctx, *, query: str):
        """Plays audio to a voice channel. Accepts both local filenames or YouTube URLs."""
        embed = getembed("Bakerbot: Now playing.", 0xFF8C00, "jingle jam 2020")

        if os.path.exists(self.mfold + query):
            audio = await discord.FFmpegOpusAudio.from_probe(self.mfold + query)
            embed.add_field(name="Local audio file.", value=query)
        else:
            audio, ytdata = await self.getytstream(query)
            embed.add_field(name="Remote audio source.", value=f"[{ytdata['title']}](https://youtube.com/watch?v={ytdata['id']})")

        ctx.voice_client.play(audio)
        await ctx.send(embed=embed)

    @commands.command()
    async def join(self, ctx):
        """Joins a voice channel."""
        if ctx.voice_client is not None: 
            if ctx.author.voice: await ctx.voice_client.move_to(ctx.author.voice.channel)
            else: await ctx.send("You are not connected to a voice channel.")
        elif ctx.author.voice: await ctx.author.voice.channel.connect()
        else: await ctx.send("You are not connected to a voice channel.")

    @commands.command(aliases=["dc"])
    async def disconnect(self, ctx):
        """Disconnects Bakerbot from any voice channels."""
        if ctx.voice_client: await ctx.voice_client.disconnect()

    async def getytstream(self, query: str):
        if not validators.url(query): query = f"ytsearch:{query}"
        data = await self.bot.loop.run_in_executor(None, lambda: self.ytdl.extract_info(query, download=False))
        if "entries" in data: data = data["entries"][0]
        audio = await discord.FFmpegOpusAudio.from_probe(data["url"], options=ffmpegopt)
        return (audio, data)

    @play.before_invoke
    async def ensureconnection(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice: await ctx.author.voice.channel.connect()
            else: await ctx.send("You are not connected to a voice channel.")
        elif ctx.voice_client.is_playing(): ctx.voice_client.stop()

def setup(bot): bot.add_cog(voice(bot))
