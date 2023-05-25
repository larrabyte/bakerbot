from .commands import *

import bot

async def setup(bot: bot.Bot):
    cog = Minecraft(bot)
    await bot.add_cog(cog)
