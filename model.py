import exceptions
import utilities

import discord.ext.commands as commands
import importlib
import aiohttp
import ujson
import sys

class Bakerbot(commands.Bot):
    def __init__(self, *args: list, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.session = aiohttp.ClientSession()

        with open("secrets.json", "r") as file:
            self.secrets = ujson.load(file)

    def reload(self) -> None:
        """Reloads the bot's internal state without logging out of Discord."""
        with open("secrets.json", "r") as file:
            self.secrets = ujson.load(file)

        reloadables = [module for name, module in sys.modules.items() if name.startswith("backends.")]
        extensions = [extension for extension in self.extensions.keys()]

        # Add any special files to the reloadables list.
        reloadables.append(exceptions)
        reloadables.append(utilities)

        for reloadable in reloadables:
            importlib.reload(reloadable)

        for extension in extensions:
            self.reload_extension(extension)

    def run(self) -> None:
        """Starts the bot. This should be the last function that is called."""
        if "discord-token" not in self.secrets:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        token = self.secrets["discord-token"]
        super().run(token)
