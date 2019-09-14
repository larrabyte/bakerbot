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