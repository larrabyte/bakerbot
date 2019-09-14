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
        await self.join(ctx)

def setup(bot): bot.add_cog(voice(bot))