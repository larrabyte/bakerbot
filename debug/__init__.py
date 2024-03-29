from .commands import *
from .errors import *

import keychain
import discord
import logging
import bot

async def setup(bot: bot.Bot):
    logger = logging.getLogger(f"bakerbot.{__package__}")
    guild = discord.Object(keychain.DEBUG_GUILD)
    cog = Debug(bot, logger)

    await bot.add_cog(cog, guild=guild)
    bot.on_command_error = on_command_error
    bot.tree.on_error = on_application_error
    logger.info(f"Custom command error handlers set.")
