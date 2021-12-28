import bootlogo
import model

import discord
import pathlib

if __name__ == "__main__":
    print(bootlogo.bootlogo)

    # Setup Discord API intents.
    intents = discord.Intents.default()
    intents.presences = False
    intents.typing = False
    intents.members = True

    # Setup the bot's activity.
    ver = discord.version_info
    name = f"discord.py v{ver.major}.{ver.minor}.{ver.micro}"
    activity = discord.Streaming(name=name, url="https://twitch.tv/larrabyte")

    # Instantiate the bot with the required arguments.
    bot = model.Bakerbot(help_command=None, case_insensitive=True, intents=intents, activity=activity)

    # Load extra extensions that reside in the root directory so that they can be
    # reloaded using bot.reload_extension(). They are still imported as modules.
    for extension in ("database", "exceptions", "utilities"):
        bot.load_extension(extension)

    # Load extensions from command group/backend folders.
    for folder in ("backends", "cogs", "local"):
        for path in pathlib.Path(folder).glob("*.py"):
            bot.load_extension(f"{folder}.{path.stem}")

    print("main(): bakerbot starting...")
    bot.run()
