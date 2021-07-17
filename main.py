import discord
import pathlib
import model

if __name__ == "__main__":
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
    bot = model.Bakerbot(command_prefix="$",
                           help_command=None,
                           case_insensitive=True,
                           intents=intents,
                           activity=activity)

    # Load extensions from the cogs folder.
    for path in pathlib.Path("cogs").glob("*.py"):
        bot.load_extension(f"cogs.{path.stem}")

    bot.run()
