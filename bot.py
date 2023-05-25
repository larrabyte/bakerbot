import discord.ext.commands as commands

import discord
import aiohttp

class Bot(commands.Bot):
    """A minimally extended commands.Bot subclass."""
    def __init__(self, session: aiohttp.ClientSession):
        # Since we have no text-based commands, the command prefix doesn't really matter.
        super().__init__(command_prefix="$", help_command=None, intents=discord.Intents.all())
        self.session = session
