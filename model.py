import exceptions
import utilities

from discord.ext import commands
import importlib
import aiohttp
import ujson

class Bakerbot(commands.Bot):
    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.session = aiohttp.ClientSession()
        self.secrets = self.spice()

    def spice(self) -> dict:
        """Returns the contents of `secrets.json` as a dictionary."""
        with open("secrets.json", "r") as file:
            return ujson.load(file)

    def reload(self) -> None:
        """Reloads the bot's internal state without logging out of Discord."""
        self.secrets = self.spice()

        for module in (exceptions, utilities):
            importlib.reload(module)

        for extension in list(self.extensions.keys()):
            self.reload_extension(extension)

    def run(self) -> None:
        """Starts the bot. This should be the last function that is called."""
        if "discord-token" not in self.secrets:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        token = self.secrets["discord-token"]
        super().run(token)
