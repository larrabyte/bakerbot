import model

import discord
import pathlib
import ujson
from bootlogo import bootlogo
import os


if __name__ == "__main__":
    print("Baker Bot Starting....")
    bootlogo()

    # Setup Discord API intents.
    intents = discord.Intents.default()
    intents.presences = False
    intents.typing = False
    intents.members = True
    os.environ.baker_secrets = ujson.load(open('secrets.json'))
    for key, value in os.environ.baker_secrets.items():
        print(f"{key}: {value}")

    # Setup the bot's activity.
    ver = discord.version_info
    name = f"discord.py v{ver.major}.{ver.minor}.{ver.micro}"
    activity = discord.Streaming(name=name, url="https://twitch.tv/larrabyte")

    # Instantiate the bot with the required arguments.
    command_prefix = os.environ.baker_secrets.get('command-prefix',"*")
    bot = model.Bakerbot(command_prefix=command_prefix, help_command=None, case_insensitive=True, intents=intents, activity=activity)

    # Load extra extensions that reside in the root directory so that they can be
    # reloaded using bot.reload_extension(). They are still imported as modules.
    for extension in ("database", "exceptions", "utilities"):
        bot.load_extension(extension)

    # Load extensions from command group/backend folders.
    for folder in ("backends", "cogs", "local"):
        for path in pathlib.Path(folder).glob("*.py"):
            bot.load_extension(f"{folder}.{path.stem}")

    print("Imports done!")
    bot.run()
