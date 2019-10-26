"""Implements voice capabilities using `PyNaCl`."""
from discord.ext import commands
import utilities as util
import discord
import os

class voice(commands.Cog):
    def __init__(self, bot):
        self.ffexec = "./ffmpeg/bin/ffmpeg.exe"
        self.ffmusic = "./ffmpeg/music/"
        self.bot = bot

    async def join(self, user):
        vclient = user.guild.voice_client
        if vclient == None or not vclient.is_connected(): await user.voice.channel.connect()
        elif vclient.channel != user.voice.channel: await vclient.move_to(user.voice.channel)

    async def play(self, guildclient, filepath):
        audio = discord.FFmpegPCMAudio(executable=self.ffexec, source=filepath)
        if guildclient.is_playing(): guildclient.stop()
        guildclient.play(audio, after=None)

    def fetchfiles(self):
        embed = util.getembed("Bakerbot: Files found in `./ffmpeg/music`:", 0xE39CF7, "fredbot says hello")
        for files in os.listdir("./ffmpeg/music"): embed.add_field(name=files, value=u"nigganigganigganigga")
        return embed

    @commands.command()
    async def musiclist(self, ctx):
        """What's in the musical pocket?"""
        await ctx.send(embed=self.fetchfiles())

    @commands.command(aliases=["join"])
    async def dujoin(self, ctx):
        """Makes the Bakerbot join your voice channel."""
        await self.join(ctx.author)

    @commands.command(aliases=["disconnect", "dc"])
    async def dudc(self, ctx):
        """Disconnects from the current channel."""
        await ctx.guild.voice_client.disconnect()

    @commands.command(aliases=["play"])
    async def duplay(self, ctx, inputstr: str=None):
        """Let's get some music going on in here! Plays local files or YouTube videos."""
        if not ctx.guild.voice_client or ctx.guild.voice_client.is_connected(): await self.join(ctx.author)

        if inputstr == None:
            await ctx.send(embed=self.fetchfiles())
            reply = await self.bot.wait_for("message", check=lambda msg: msg.author == ctx.author)
            await self.play(ctx.guild.voice_client, self.ffmusic + reply.content)
        elif not inputstr[:4] == "http": await self.play(ctx.guild.voice_client, self.ffmusic + inputstr)
        else: await self.play(ctx, util.downloadyt(inputstr))

    @commands.command()
    async def resume(self, ctx):
        """Resumes the music if there is anything to resume."""
        ctx.guild.voice_client.resume()

    @commands.command()
    async def pause(self, ctx):
        """Pauses the music if there is any."""
        ctx.guild.voice_client.pause()

    @commands.command()
    async def stop(self, ctx):
        """Stops playing music if there is any."""
        ctx.guild.voice_client.stop()

def setup(bot): bot.add_cog(voice(bot))