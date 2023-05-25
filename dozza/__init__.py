from .commands import *

import bot

async def setup(bot: bot.Bot):
    cog = Dozza(bot)
    await bot.add_cog(cog)
