import discord.ext.commands as commands

import keychain
import discord
import asyncio
import logging

async def main():
    discord.utils.setup_logging(level=logging.INFO)

    ver = discord.version_info
    logger = logging.getLogger("bakerbot.main")
    logger.info(f"Using discord.py v{ver.major}.{ver.minor}.{ver.micro} {ver.releaselevel}.")

    # With no way to read message content, the command prefix doesn't really matter.
    async with commands.Bot(command_prefix="$", intents=discord.Intents.default()) as bot:
        await bot.start(keychain.DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
