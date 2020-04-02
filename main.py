from discord.ext import commands
from btoken import token
import discord

bot = commands.Bot(command_prefix="$", help_command=None, case_insensitive=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}, ID: {bot.user.id}.")
    await bot.change_presence(activity=discord.Game("with ur mum lol"))

if __name__ == "__main__":
    bot.run(token)
