from .commands import *

import discord.ext.commands as commands

async def setup(bot: commands.Bot):
    session = aiohttp.ClientSession(raise_for_status=True)
    cog = Wolfram(bot, session)
    await bot.add_cog(cog)
