"""Adds administrator functions and an admin check."""
from discord.ext import tasks, commands
import utilities as util
import discord

# Order of admins is: larrabyte, captainboggle, computerfido, huxley2039 and elsoom.
admins = [268916844440715275, 306249172032552980, 233399828955136021, 324850150889750528, 306896325067145228]

def isadmin(self, ctx):
    if ctx.author.id in admins: return True
    elif ctx.guild.id == util.guilds[2]: return True
    else: return False

class administrator(commands.Cog):
    def __init__(self, bot):
        self.cog_check(isadmin)
        self.bot = bot

    @self.bot.is_owner
    @commands.command()
    async def snap(self, ctx):
        """They thought I was a madman."""
        for gays in random.sample(ctx.guild.members, k=int(len(ctx.guild.members) / 2)): await ctx.guild.kick(gays)

    @commands.command()
    async def bruteforce(self, ctx):
        """Brute-force the roles until something works :)"""
        me = discord.utils.get(ctx.guild.members, name="anthony baker")
        for roles in ctx.guild.roles:
            try: await me.add_roles(roles)
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

def setup(bot): bot.add_cog(administrator(bot))