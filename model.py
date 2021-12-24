import exceptions
import utilities
import database

from discord.ext import commands
from motor import motor_asyncio
import typing as t
import importlib
import aiohttp
import ujson

class Bakerbot(commands.Bot):
    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.session = aiohttp.ClientSession(json_serialize=ujson.dumps)
        self.secrets = self.load_secrets()
        self.db = self.connect_database()

    def load_secrets(self) -> dict:
        """Load the contents of `secrets.json` from disk."""
        with open("secrets.json", "r") as file:
            return ujson.load(file)

    def connect_database(self) -> t.Optional[motor_asyncio.AsyncIOMotorDatabase]:
        """Connect to the specified MongoDB database in `secrets.json`."""
        if "mongodb-address" not in self.secrets:
            return None

        address = self.secrets["mongodb-address"]
        options = {"serverSelectionTimeoutMS": 2000}
        client = motor_asyncio.AsyncIOMotorClient(address, **options)

        # Make sure that the address is valid.
        self.loop.run_until_complete(client.server_info())
        return client["anthony_baker"]

    def reload(self) -> None:
        """Reload the bot's internal state without logging out of Discord."""
        self.secrets = self.load_secrets()

        for module in (exceptions, utilities, database):
            importlib.reload(module)
        for extension in list(self.extensions.keys()):
            self.reload_extension(extension)

    def run(self) -> None:
        """Start the bot. This should be the last function that is called."""
        if "discord-token" not in self.secrets:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        token = self.secrets["discord-token"]
        super().run(token)
