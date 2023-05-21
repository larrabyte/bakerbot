from .commands import *

import discord.ext.commands as commands

import logging

async def setup(bot: commands.Bot):
    logger = logging.getLogger(f"bakerbot.{__package__}")
    cog = Minecraft(bot, logger)
    await bot.add_cog(cog)
