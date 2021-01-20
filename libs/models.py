from discord.ext import commands
from libs.mangadex import Mangadex

import wavelink
import aiohttp

class Bakerbot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.session = aiohttp.ClientSession()
        self.wavelink = wavelink.Client(bot=self)

        # Create tasks to setup other libraries.
        self.loop.create_task(Mangadex.setup(session=self.session))
