import discord.ext.commands as commands
import importlib
import utilities
import aiohttp
import json

class Bakerbot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.session = aiohttp.ClientSession()
        self.secrets = self.loadsecrets()
        self.utils = self.loadutils()

    def loadsecrets(self) -> dict:
        """Refreshes the bot's secrets dictionary."""
        with open("secrets.json", "r") as file:
            return json.load(file)

    def loadutils(self) -> utilities:
        """Refreshes the bot's utility module."""
        return importlib.reload(utilities)

    def run(self) -> None:
        """Starts the bot."""
        if (token := self.secrets.get("discord-token", None)) is None:
            raise RuntimeError("discord-token not found in secrets.json.")

        super().run(token)
