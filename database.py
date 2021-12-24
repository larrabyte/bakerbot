import model

import motor.motor_asyncio as motor
import dataclasses
import datetime
import discord
import copy

@dataclasses.dataclass
class StarboardMessage:
    """The database starboard message template."""
    message_id: int
    author_id: int
    channel_id: int
    guild_id: int
    reply_target_id: int | None
    timestamp: datetime.datetime
    message_content: str
    attachment_urls: list[str]
    reaction_count: int

    @classmethod
    async def get(cls, identifier: int) -> "StarboardMessage | None":
        """Get the StarboardMessage instance for a message from the database. Returns `None` if the message is not in the database."""
        collection = Backend.db["starboarded_messages"]
        query = {"message_id": identifier}
        document = await collection.find_one(query, {"_id": False})

        if document is None:
            return None

        return cls(**document)

    @classmethod
    async def new(cls, message: discord.Message, reactions: int) -> "StarboardMessage":
        """Create a new instance of `StarboardMessage` for a message with a specified reaction count."""
        attachment_urls = [attachment.url for attachment in message.attachments]
        sticker_urls = [sticker.url for sticker in message.stickers]

        return cls(
            message_id=message.id,
            author_id=message.author.id,
            channel_id=message.channel.id,
            guild_id=message.guild.id,
            reply_target_id=message.reference.message_id if message.reference is not None else None,
            timestamp=message.created_at,
            message_content=message.content,
            attachment_urls=attachment_urls + sticker_urls,
            reaction_count=reactions
        )

    async def write(self) -> None:
        """Write this StarboardMessage instance to the database."""
        starboard = Backend.db["starboarded_messages"]
        query = {"message_id": self.message_id}
        document = dataclasses.asdict(self)
        await starboard.replace_one(query, document, upsert=True)

@dataclasses.dataclass
class GuildConfiguration:
    """The database guild configuration template."""
    guild_id: int
    starboard_threshold: int
    starboard_channel_id: int | None
    starboard_emoji_id: int | None
    who_asked_enabled: bool
    message_resender_enabled: bool
    starboard_enabled: bool
    ignored_channels: list[int]

    @staticmethod
    async def ensure(identifier: int) -> "GuildConfiguration":
        """"Return the starboard configuration for a guild (inserting a new one if necessary)."""
        if (config := await GuildConfiguration.get(identifier)) is not None:
            # If a configuration was already in the database, return it.
            return config

        # Otherwise, create a new one, write it to the database and return that instead.
        config = GuildConfiguration.new(identifier)
        await config.write()
        return config

    @classmethod
    def new(cls, identifier: int) -> "GuildConfiguration":
        """Create a new instance of `GuildConfiguration` for a guild with ID `identifier`."""
        return cls(
            guild_id=identifier,
            starboard_threshold=3,
            starboard_channel_id=None,
            starboard_emoji_id=None,
            who_asked_enabled=False,
            message_resender_enabled=False,
            starboard_enabled=False,
            ignored_channels=[]
        )

    @classmethod
    async def get(cls, identifier: int) -> "GuildConfiguration | None":
        """Get the GuildConfiguration instance for a guild from the database. Returns `None` if the guild is not in the database."""
        collection = Backend.db["guild_settings"]
        query = {"guild_id": identifier}
        document = await collection.find_one(query, {"_id": False})

        if document is None:
            return None

        # Find the set of fields that are defined in the dataclass but not present in the document.
        fields = set((field.name for field in dataclasses.fields(cls)))
        section = set(document.keys())
        construct = fields - section

        # Add these fields to the document using values from a template.
        template = dataclasses.asdict(GuildConfiguration.new(0))

        for field in construct:
            obj = copy.deepcopy(template[field])
            document[field] = obj

        return cls(**document)

    async def write(self) -> None:
        """Write the guild's configuration to the database."""
        collection = Backend.db["guild_settings"]
        query = {"guild_id": self.guild_id}
        document = dataclasses.asdict(self)
        await collection.replace_one(query, document, upsert=True)

    def starboard_ready(self) -> bool:
        """Check whether this guild has its starboard configuration set."""
        members = (self.starboard_channel_id, self.starboard_emoji_id)
        return self.starboard_enabled == True and None not in members

class Backend:
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        cls.db_object = bot.db
        cls.db_address = bot.secrets.get("mongodb-address", None)

    @classmethod
    @property
    def db(cls) -> motor.AsyncIOMotorDatabase:
        """Return the bot's database object, throws an exception if not available."""
        if cls.db_object is None:
            address = cls.db_address or "No address specified."
            raise DatabaseNotConnected(address)

        return cls.db_object

class DatabaseNotConnected(Exception):
    """Raised when the database object is `None`."""
    pass

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
