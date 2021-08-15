import discord.ext.commands as commands
import importlib
import utilities
import aiohttp
import ujson

class Bakerbot(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.session = aiohttp.ClientSession()
        self.secrets = Bakerbot.load_secrets()
        self.utils = Bakerbot.load_utils()

    @staticmethod
    def load_secrets() -> dict:
        """Refreshes the bot's secrets dictionary."""
        with open("secrets.json", "r") as file:
            return ujson.load(file)

    @staticmethod
    def load_utils() -> utilities:
        """Refreshes the bot's utility module."""
        return importlib.reload(utilities)

    def run(self) -> None:
        """Starts the bot."""
        if (token := self.secrets.get("discord-token", None)) is None:
            raise RuntimeError("discord-token not found in secrets.json.")

        super().run(token)
