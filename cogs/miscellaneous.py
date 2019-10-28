"""Various fun commands that aren't harmful in any way."""
from discord.ext import commands
import utilities as util
import subprocess
import asyncio
import discord
import random
import math

class miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bruteforce(self, ctx, user: discord.Member=None):
        """Brute-force the roles until something works :)"""
        if not user: user = discord.utils.get(ctx.guild.members, name="anthony baker")
        await user.add_roles(ctx.guild.roles)

    @commands.command()
    async def historyfetch(self, ctx):
        """Fetches the message history of the guild. Does not record bot messages."""        
        with open("./data/data.txt", "w") as datafile:
            for channel in ctx.guild.text_channels:
                async for message in channel.history(limit=None):
                    if not message.author.bot:
                        try: datafile.write(message.content + "\n")
                        except Exception: pass

                print(channel.name + " has been recorded.")
        await ctx.send("All channels recorded to data.txt.")

    @commands.command()
    async def typingtoinfinityandbeyond(self, ctx):
        """To infinity, and beyond!"""
        async with ctx.channel.typing(): await asyncio.sleep(math.inf)

    @commands.command(aliases=["ng"])
    async def nigga(self, ctx, user: discord.Member):
        """big n-word energy"""
        voice = self.bot.get_cog("voice")
        await user.edit(voice_channel=random.choice(ctx.guild.voice_channels))
        await voice.unifiedplay(ctx.author, "./ffmpeg/music/reallynigga.mp3")
        await asyncio.sleep(2)
        await user.edit(voice_channel=None)
        await ctx.guild.voice_client.disconnect()

    @commands.command()
    async def ringring(self, ctx):
        """Ring ring ring ring ring ring, BANANA PHONE!"""
        songs = ["bananaphone-earrape.mp3", "bananaphone.webm", "bananaphone-nightcore.webm"]
        await self.bot.get_cog("voice").unifiedplay(ctx.author, "./ffmpeg/music/" + random.choice(songs))

    # @commands.command()
    # async def echotoall(self, ctx, *, message):
    #     """Echos `message` to all channels that aren't forbidden."""
    #     communists = util.fetchbannedchannels(ctx)
    #     for channels in ctx.guild.text_channels:
    #         if not channels.id in communists:
    #             try: await channels.send(message)
    #             except Exception: pass
    #             else: await asyncio.sleep(1)

def setup(bot): bot.add_cog(miscellaneous(bot))