from .commands import *

import bot

async def setup(bot: bot.Bot):
    cog = Wolfram(bot)
    await bot.add_cog(cog)
