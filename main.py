from discord.ext import commands
from utilities import *
from glob import glob
from btoken import *
import discord

bot = commands.Bot(command_prefix="$", help_command=None, case_insensitive=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}, ID: {bot.user.id}.")
    await bot.change_presence(activity=discord.Game("with the API."))

if __name__ == "__main__":
    for files in glob("cogs/*.py"):
        try: bot.load_extension(file2ext(files))
        except Exception: raise

    bot.run(token)
