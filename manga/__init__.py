from .commands import *

import discord.ext.commands as commands

import aiohttp

async def setup(bot: commands.Bot):
    session = aiohttp.ClientSession(raise_for_status=True)
    cog = Manga(bot, session)
    await bot.add_cog(cog)
