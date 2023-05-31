import keychain
import discord
import asyncio
import logging
import pathlib
import aiohttp
import asyncpg
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

    async with (
        aiohttp.ClientSession(raise_for_status=True) as session,
        asyncpg.create_pool(keychain.POSTGRES_URL) as pool,
        bot.Bot(session, pool) as client
    ):

        packages = (
            path for path in pathlib.Path(".").iterdir()
            if path.is_dir() and not path.name.startswith((".", "_"))
        )

        for package in packages:
            await client.load_extension(package.name)
            logger.info(f"Loaded extension {package.name}.")

        await client.start(keychain.DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
