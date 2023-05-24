from .commands import *

import discord.ext.commands as commands

async def setup(bot: commands.Bot):
    cog = Minecraft(bot)
    await bot.add_cog(cog)
