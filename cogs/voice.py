"""Implements voice capabilities using `PyNaCl`."""
from discord.ext import commands
import utilities as util
import discord
import os

class voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def join(self, ctx):
        guildvoice = ctx.guild.voice_client
        if guildvoice == None or not guildvoice.is_connected(): await ctx.author.voice.channel.connect()
        elif guildvoice.channel != ctx.author.voice.channel: await guildvoice.move_to(ctx.author.voice.channel)
        else: await ctx.send("um i cant do anything help pls " + ctx.author.mention)

    @commands.command(aliases=["join"])
    async def discorduserjoin(self, ctx):
        """Makes the Bakerbot join your voice channel."""
        await self.join(ctx)

    @commands.command(aliases=["disconnect", "dc"])
    async def discorduserdc(self, ctx):
        """Disconnects from the current channel."""
        await ctx.guild.voice_client.disconnect()

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