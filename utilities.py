from discord.ext import commands
import discord
import os

def fetchcogs():
    """Returns list of files found in `./cogs`. Files retain suffixes, such as `py`."""
    return [files for files in os.listdir("./cogs") if files.endswith(".py")]

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