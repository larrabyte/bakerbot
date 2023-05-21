from .commands import *
from .backend import *

import discord.ext.commands as commands

import logging

async def setup(bot: commands.Bot):
    logger = logging.getLogger(f"bakerbot.{__package__}")
    session = aiohttp.ClientSession(raise_for_status=True)
    cog = Dozza(bot, logger, session)
    await bot.add_cog(cog)
