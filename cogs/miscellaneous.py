"""Various fun commands that aren't harmful in any way."""
from discord.ext import tasks, commands
import utilities as util
import subprocess
import asyncio
import discord
import random
import math

@tasks.loop(seconds=1.0)
async def spamloop(ctx, message):
    await ctx.send(message)

class miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bananas = ["bananaphone-earrape.mp3", "bananaphone.webm", "bananaphone-nightcore.webm"]
        self.spamming = False
        self.giving = False
        self.bot = bot

    @commands.command()
    async def giveaway(self, ctx, *, prize):
        """giveaway algorithm no bias sanders for president 2020"""
        if not self.giving:
            cache = random.sample(ctx.guild.members, 5)
            plstr = "\n".join([user.mention for user in cache])
            embed = util.getembed(f"The Bakerbot Lottery: Prize of {prize}", 0xFF8C00, "sponsored by the pharmaceutical industry")
            embed.add_field(name="Potential Winners", value=plstr, inline=False)
            messg = await ctx.send(embed=embed)

            self.giving = True
            await ctx.send("Choose one potential lottery winner to take the L!")
            reply = await self.bot.wait_for("message", check=lambda msg: msg.author == ctx.author)
            nache = [member for member in cache if member.mention != reply.content]
            npstr = "\n".join([user.mention for user in nache])
            await ctx.send("now performing extremely complicated math to find ourselves a winner winner chicken dinner")
            embed.set_field_at(0, name="Potential Winners", value=npstr, inline=False)
            await messg.edit(embed=embed)
            await asyncio.sleep(15)

            embed = util.getembed("The Bakerbot Lottery: WINNER WINNER CHICKEN DINNER", 0xFF8C00,"sponsored by the pharmaceutical industry")
            embed.add_field(name="code is fucked and so is ur mum :point_right: :sunglasses: :point_right:", value=f"{random.choice(nache).mention} wins {prize}")
            await ctx.send(embed=embed)
            self.giving = False

        else: await ctx.send("giveaway in progress shut the fuck up")

    @commands.command()
    async def yougotspam(self, ctx, *, message):
        """You've got SPAM(tm)! You've got SPAM(tm)!"""
        if self.spamming: spamloop.stop()
        else: await spamloop.start(ctx)
        self.spamming = not self.spamming

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

                print(f"{channel.name} has been recorded.")
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
        await self.bot.get_cog("voice").unifiedplay(ctx.author, f"./ffmpeg/music/{random.choice(self.bananas)}")

def setup(bot): bot.add_cog(miscellaneous(bot))