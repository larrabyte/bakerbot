from libs.wikipedia import Wikipedia
from libs.mangadex import Mangadex
from libs.wolfram import Wolfram
from discord.ext import commands
from libs.jisho import Jisho

import wavelink
import aiohttp

class Bakerbot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.session = aiohttp.ClientSession()
        self.wavelink = wavelink.Client(bot=self)

        # Create tasks to setup other libraries.
        self.loop.create_task(Mangadex.setup(session=self.session))
        self.loop.create_task(Wolfram.setup(session=self.session, signing=True))
        self.loop.create_task(Jisho.setup(session=self.session))
        self.loop.create_task(Wikipedia.setup(session=self.session))
