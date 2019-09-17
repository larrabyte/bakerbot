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

    async def join(self, ctx):
        guildvoice = ctx.guild.voice_client
        if guildvoice == None or not guildvoice.is_connected(): await ctx.author.voice.channel.connect()
        elif guildvoice.channel != ctx.author.voice.channel: await guildvoice.move_to(ctx.author.voice.channel)
        else: await ctx.send("um i cant do anything help pls " + ctx.author.mention)

    async def play(self, ctx, filepath):
        audio = discord.FFmpegPCMAudio(executable=self.ffexec, source=filepath)
        guildvoice = ctx.guild.voice_client
        if guildvoice.is_playing(): guildvoice.stop()
        guildvoice.play(audio, after=None)

    def fetchfiles(self):
        embed = util.getembed("Bakerbot: Files found in `./ffmpeg/music`:", 0xE39CF7, "fredbot says hello")
        for files in os.listdir("./ffmpeg/music"): embed.add_field(name=files, value=u"nigganigganigganigga")
        return embed

    @commands.command()
    async def musiclist(self, ctx):
        """What's in the musical pocket?"""
        await ctx.send(embed=self.fetchfiles())

    @commands.command(aliases=["join"])
    async def discorduserjoin(self, ctx):
        """Makes the Bakerbot join your voice channel."""
        await self.join(ctx)

    @commands.command(aliases=["disconnect", "dc"])
    async def discorduserdc(self, ctx):
        """Disconnects from the current channel."""
        await ctx.guild.voice_client.disconnect()

    @commands.command(aliases=["play"])
    async def discorduseruniversalplay(self, ctx, inputstr: str=None):
        """Let's get some music going on in here! Plays local files or YouTube videos."""
        if not ctx.guild.voice_client or ctx.guild.voice_client.is_connected(): await self.join(ctx)

        if inputstr == None or not inputstr[:4] == "http":
            await ctx.send(embed=self.fetchfiles())
            reply = await self.bot.wait_for("message", check=lambda msg: msg.author == ctx.author)
            await self.play(ctx, self.ffmusic + reply.content)
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