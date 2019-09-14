from discord.ext import commands
import discord
import random
import string
import os

# Guild order: Admin Abuse 2, Team Magic and the Bakerbot Guild.
# Banned channels for Team Magic: #rules-and-announcements and #meta
guilds = [554211911697432576, 473426067823263749, 620168587759583243]

def fetchcogs():
    """Returns list of files found in `./cogs`. Files retain suffixes, such as `py`."""
    return [files for files in os.listdir("./cogs") if files.endswith(".py")]

def randstr(length):
    """Returns `length` random characters."""
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))

def fetchbannedchannels(ctx):
    """Returns a list of channels the bot should not speak in."""
    if ctx.guild.id == guilds[1]: return [473433493796421652, 482504425328476161]
    else: return None

def getcogname(filename):
    """Returns proper cog name to allow extension loading.\n
    Example: `errorhandler.py` >> `cogs.errorhandler`"""
    filename = filename.replace(".py", "")
    return "cogs." + filename

def getembed(title, colour, footerText: str=None):
    """Returns a discord Embed with `title`, `colour` and optionally, `footerText`.\n
       Also adds a picture of someone from Airbus called Anthony Baker."""
    embed = discord.Embed(title=title, color=colour)
    embed.set_thumbnail(url="https://airbus-h.assetsadobe2.com/is/image/content/dam/channel-specific/website-/us/management/anthony-baker.jpg?wid=1000&qlt=85,0")
    if footerText: embed.set_footer(text=footerText)
    else: embed.set_footer(text="creeper, aww man")
    return embed