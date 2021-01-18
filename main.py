from discord.ext import commands
from pathlib import Path
import discord
import logging
import btoken

if __name__ == "__main__":
    # Discord intents (helps reduce API requests).
    intents = discord.Intents.default()
    intents.presences = False
    intents.typing = False
    intents.members = True

    # Setup the logger to output messages to log.txt.
    handler = logging.FileHandler(filename=Path("./log.txt"), encoding="utf-8", mode="w")
    handler.setFormatter(logging.Formatter("[%(levelname)s @ %(asctime)s] %(message)s"))
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)

    # Bot object, kinda important to keep around :p
    bot = commands.Bot(command_prefix="$", help_command=None, case_insensitive=True, intents=intents)

    # Load extensions from the cogs folder.
    for path in Path("./cogs").glob("**/*.py"):
        try: bot.load_extension(f"cogs.{path.stem}")
        except: raise

    # Start the bot.
    bot.run(btoken.token)
