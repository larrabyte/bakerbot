from .commands import *
from .errors import *

import discord.ext.commands as commands

import keychain
import discord
import logging

async def setup(bot: commands.Bot):
    logger = logging.getLogger(f"bakerbot.{__package__}")
    guild = discord.Object(keychain.DEBUG_GUILD)
    cog = Debug(bot, logger)

    await bot.add_cog(cog, guild=guild)
    bot.tree.on_error = on_application_error
    logger.info(f"Custom application command error handler set.")
