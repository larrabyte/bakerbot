from discord.ext import commands
from btoken import token
from glob import glob
import discord

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="$", help_command=None, case_insensitive=True, intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}, ID: {bot.user.id}.")
    await bot.change_presence(activity=discord.Game("with the API."))

if __name__ == "__main__":
    for filename in glob("cogs/*.py"):
        filename = filename.replace("\\", ".").replace("/", ".").replace(".py", "")
        try: bot.load_extension(filename)
        except Exception: raise

    bot.run(token)
