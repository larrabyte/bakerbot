from discord.ext import commands
import utilities as util
import maintoken
import discord

bot = commands.Bot(command_prefix="$", help_command=None, case_insensitive=True)

@bot.event
async def on_ready():
    print("Logged in as: " + bot.user.name + "\nBot ready, ID: " + str(bot.user.id))
    await bot.change_presence(activity=discord.Game("$help for help."))

if __name__ == "__main__":
    for files in util.fetchcogs():
        try: bot.load_extension(util.getcogname(files))
        except Exception: raise

    bot.run(maintoken.token)