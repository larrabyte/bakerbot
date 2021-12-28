from discord.ext import commands
import motor.motor_asyncio as motor
import aiohttp
import typing
import ujson

class Bakerbot(commands.Bot):
    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        self.session = aiohttp.ClientSession(json_serialize=ujson.dumps)
        self.secrets = self.load_secrets()
        prefix = self.secrets.get("command-prefix", "$")
        super().__init__(command_prefix=prefix, *args, **kwargs)
        self.db = self.connect_database()

    def load_secrets(self) -> dict:
        """Load the contents of `secrets.json` from disk."""
        with open("secrets.json", "r") as file:
            secrets = ujson.load(file)

            print("model.Bakerbot.load_secrets(): secrets read as follows.")
            for key, value in secrets.items():
                print(f"    {key}: {value}")

            print("")
            return secrets

    def connect_database(self) -> motor.AsyncIOMotorDatabase | None:
        """Return the bot's database from the specified MongoDB address in `secrets.json`."""
        if "mongodb-address" not in self.secrets:
            return None

        address = self.secrets["mongodb-address"]
        options = {"serverSelectionTimeoutMS": 2000}
        client = motor.AsyncIOMotorClient(address, **options)

        # Make sure that the address is valid. If the database
        # `anthony_baker` doesn't exist, just let the exception propagate.
        self.loop.run_until_complete(client.server_info())
        return client["anthony_baker"]

    def reload(self) -> None:
        """Reload the bot's internal state without logging out of Discord."""
        self.secrets = self.load_secrets()
        for extension in list(self.extensions.keys()):
            self.reload_extension(extension)

    def run(self) -> None:
        """Start the bot. This should be the last function that is called."""
        if "discord-token" not in self.secrets:
            raise SecretNotFound("discord-token not specified in secrets.json.")

        token = self.secrets["discord-token"]
        super().run(token)

class SecretNotFound(Exception):
    """Raised whenever a secret cannot be found."""
    pass
