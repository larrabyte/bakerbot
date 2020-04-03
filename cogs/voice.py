from discord.ext import tasks, commands
from utilities import *
from glob import glob
import discord
import asyncio
import os

class voice(commands.Cog):
    """Implements voice capabilities."""

    def __init__(self, bot):
        self.mfold = "data/music/"
        self.bot = bot

    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a local audio file."""
        audio = discord.FFmpegOpusAudio.from_probe(self.mfold + query)
        ctx.voice_client.play(audio)

        embed = getembed("Bakerbot: Now playing.", 0xFF8C00, "jingle jam 2020")
        embed.add_field(name="Local music file.", value=f"{query}: {ctx.author.mention}")
        await ctx.send(embed=embed)

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
    async def ensureconnection(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice: await ctx.author.voice.channel.connect()
            else: await ctx.send("You are not connected to a voice channel.")
        elif ctx.voice_client.is_playing(): ctx.voice_client.stop()

def setup(bot): bot.add_cog(voice(bot))
