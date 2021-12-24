import database
import model

import discord
import pathlib

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
    bot = model.Bakerbot(command_prefix="$", help_command=None, case_insensitive=True, intents=intents, activity=activity)

    @bot.event
    async def on_message(message: discord.Message) -> None:
        """Event handler to ignore messages from certain channels."""
        if message.guild is not None:
            config = await database.GuildConfiguration.get(message.guild.id)
            if config is None or message.channel.id in config.ignored_channels:
                return

        await bot.process_commands(message)

    # Load extensions from command group/backend folders.
    for folder in ("abcs", "backends", "cogs", "local"):
        for path in pathlib.Path(folder).glob("*.py"):
            bot.load_extension(f"{folder}.{path.stem}")

    # Load extra extensions that reside in the root directory so that they can be
    # reloaded using bot.reload_extension(). They are still imported as modules.
    for extension in ["database", "exceptions", "utilities"]:
        bot.load_extension(extension)

    bot.run()
