"""Adds administrator functions and an admin check."""
from discord.ext import tasks, commands
import utilities as util

# Order of admins is: larrabyte, captainboggle, computerfido, huxley2039 and elsoom.
admins = [268916844440715275, 306249172032552980, 233399828955136021, 324850150889750528, 306896325067145228]

def isadmin(self, userid):
    if userid in admins: return True
    else: return False

class administrator(commands.Cog):
    def __init__(self, bot):
        self.cog_check(isadmin)
        self.bot = bot

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