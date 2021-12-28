import model

import discord
import pathlib
import ujson
from bootlogo import bootlogo


if __name__ == "__main__":
    print("Baker Bot Starting....")
    bootlogo()

    # Setup Discord API intents.
    intents = discord.Intents.default()
    intents.presences = False
    intents.typing = False
    intents.members = True
    secrets = ujson.load(open('secrets.json'))

    # Setup the bot's activity.
    ver = discord.version_info
    name = f"discord.py v{ver.major}.{ver.minor}.{ver.micro}"
    activity = discord.Streaming(name=name, url="https://twitch.tv/larrabyte")

    # Instantiate the bot with the required arguments.
    command_prefix = secrets.get('command-prefix',"*")
    print((f"command_prefix is '{command_prefix}'"))
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
