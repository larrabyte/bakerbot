from discord.ext import commands
from utilities import *
import youtube_dl
import discord

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

    @commands.command(aliases=["resume"])
    async def pause(self, ctx):
        """Pause/resume."""
        if ctx.voice_client:
            if ctx.voice_client.is_playing(): ctx.voice_client.pause()
            elif ctx.voice_client.is_paused(): ctx.voice_client.resume()

    @commands.command()
    async def play(self, ctx, *, query: str):
        """Plays a local audio file."""
        audio = await discord.FFmpegOpusAudio.from_probe(self.mfold + query)
        ctx.voice_client.play(audio)

        embed = getembed("Bakerbot: Now playing.", 0xFF8C00, "jingle jam 2020")
        embed.add_field(name="Local music file.", value=query)
        await ctx.send(embed=embed)

    @commands.command()
    async def stream(self, ctx, url: str):
        """Stream a YouTube URL to voice."""
        data = await self.bot.loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))
        if "entries" in data: data = data["entries"][0]
        embed = getembed("Bakerbot: Now playing.", 0xFF8C00, "jingle jam 2020", data["thumbnail"])
        embed.add_field(name="Remote YouTube video.", value=f"[{data['title']}]({data['url']})")
        audio = await discord.FFmpegOpusAudio.from_probe(data["url"], options=ffmpegopt)
        await ctx.send(embed=embed)
        ctx.voice_client.play(audio)

    @commands.command()
    async def join(self, ctx):
        """Joins a voice channel."""
        if ctx.voice_client is not None: 
            if ctx.author.voice: await ctx.voice_client.move_to(ctx.author.voice.channel)
            else: await ctx.send("You are not connected to a voice channel.")
        elif ctx.author.voice: await ctx.author.voice.channel.connect()
        else: await ctx.send("You are not connected to a voice channel.")

    @commands.command()
    async def disconnect(self, ctx):
        """Disconnects Bakerbot from any voice channels."""
        if ctx.voice_client: await ctx.voice_client.disconnect()

    @play.before_invoke
    @stream.before_invoke
    async def ensureconnection(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice: await ctx.author.voice.channel.connect()
            else: await ctx.send("You are not connected to a voice channel.")
        elif ctx.voice_client.is_playing(): ctx.voice_client.stop()

def setup(bot): bot.add_cog(voice(bot))
