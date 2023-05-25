import keychain
import discord
import asyncio
import logging
import pathlib
import aiohttp
import bot

async def main():
    discord.utils.setup_logging(level=logging.INFO)
    logger = logging.getLogger(f"bakerbot.main")

    logger.info(
        "Using discord.py v%s.%s.%s %s",
        discord.version_info.major,
        discord.version_info.minor,
        discord.version_info.micro,
        discord.version_info.releaselevel
    )

    async with aiohttp.ClientSession(raise_for_status=True) as session, bot.Bot(session) as client:
        for package in (p for p in pathlib.Path(".").iterdir() if p.is_dir() and not p.name.startswith(".")):
            await client.load_extension(package.name)
            logger.info(f"Loaded extension {package.name}.")

        await client.start(keychain.DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
