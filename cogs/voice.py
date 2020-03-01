"""Implements voice capabilities using `PyNaCl`."""
from discord.ext import commands
import utilities as util
import discord
import os

class voice(commands.Cog):
    def __init__(self, bot):
        self.ffmusic = "./ffmpeg/music/"
        self.bot = bot

    async def unifiedplay(self, user, filepath: str=None):
        gclient = user.guild.voice_client
        if gclient == None or not gclient.is_connected(): gclient = await user.voice.channel.connect()
        elif gclient.channel != user.voice.channel: await gclient.move_to(user.voice.channel)
        if gclient.is_playing(): gclient.stop()

        if filepath != None: gclient.play(discord.FFmpegPCMAudio(executable="./ffmpeg/bin/ffmpeg.exe", source=filepath), after=None)

    def fetchfiles(self):
        embed = util.getembed("Bakerbot: Files found in `./ffmpeg/music`:", 0xE39CF7, "fredbot says hello")
        embedvaluestr = ""

        for files in os.listdir(self.ffmusic): embedvaluestr += files + "\n"
        embed.add_field(name="Brug moment.", value=embedvaluestr)
        return embed

    @commands.command(aliases=["ml"])
    async def musiclist(self, ctx):
        """What's in the musical pocket?"""
        await ctx.send(embed=self.fetchfiles())

    @commands.command(aliases=["join"])
    async def dujoin(self, ctx):
        """Makes the Bakerbot join your voice channel."""
        await self.unifiedplay(ctx.author)

    @commands.command(aliases=["disconnect", "dc"])
    async def dudc(self, ctx):
        """Disconnects from the current channel."""
        await ctx.guild.voice_client.disconnect()

    @commands.command(aliases=["play"])
    async def duplay(self, ctx, inputstr: str=None):
        """Let's get some music going on in here! Plays local files or YouTube videos."""
        if ctx.message.attachments:
            await ctx.message.attachments[0].save(self.ffmusic + ctx.message.attachments[0].filename)
            await self.unifiedplay(ctx.author, self.ffmusic + ctx.message.attachments[0].filename)
        elif inputstr == None:
            await ctx.send(embed=self.fetchfiles())
            reply = await self.bot.wait_for("message", check=lambda msg: msg.author == ctx.author)
            await self.unifiedplay(ctx.author, self.ffmusic + reply.content)
        elif not inputstr[:4] == "http": await self.unifiedplay(ctx.author, self.ffmusic + inputstr)
        else: await self.unifiedplay(ctx.author, util.downloadyt(inputstr))

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