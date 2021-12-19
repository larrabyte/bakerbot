from motor import motor_asyncio
import dataclasses
import typing as t
import datetime
import discord

@dataclasses.dataclass
class StarboardMessage:
    """The database starboard message template."""
    message_id: int
    author_id: int
    channel_id: int
    guild_id: int
    reply_target_id: t.Optional[int]
    timestamp: datetime.datetime
    message_content: str
    attachment_urls: t.List[str]
    reaction_count: int

    @classmethod
    async def get(cls, db: motor_asyncio.AsyncIOMotorDatabase, identifier: int) -> t.Optional["StarboardMessage"]:
        """Get the StarboardMessage instance for a message from the database. Returns `None` if the message is not in the database."""
        collection = db["starboarded_messages"]
        query = {"message_id": identifier}
        document = await collection.find_one(query, {"_id": False})

        if document is None:
            return None

        return cls(**document)

    @classmethod
    async def new(cls, message: discord.Message, reactions: int) -> "StarboardMessage":
        """Creates a new instance of `StarboardMessage` for a message with a specified reaction count."""
        return cls(
            message_id=message.id,
            author_id=message.author.id,
            channel_id=message.channel.id,
            guild_id=message.guild.id,
            reply_target_id=message.reference.message_id if message.reference is not None else None,
            timestamp=message.created_at,
            message_content=message.content,
            attachment_urls=[attachment.url for attachment in message.attachments],
            reaction_count=reactions
        )

    async def write(self, db: motor_asyncio.AsyncIOMotorDatabase) -> None:
        """Writes this StarboardMessage instance to the database."""
        starboard = db["starboarded_messages"]
        query = {"message_id": self.message_id}
        document = dataclasses.asdict(self)
        await starboard.replace_one(query, document, upsert=True)

@dataclasses.dataclass
class GuildConfiguration:
    """Available settings for a guild."""
    guild_id: int
    starboard_threshold: int
    starboard_channel_id: t.Optional[int]
    starboard_emoji_id: t.Optional[int]
    who_asked_enabled: bool
    message_resender_enabled: bool
    starboard_enabled: bool

    @staticmethod
    async def ensure(db: motor_asyncio.AsyncIOMotorDatabase, identifier: int) -> "GuildConfiguration":
        """"Returns the starboard configuration for a guild (inserting a new one if necessary)."""
        if db is None:
            raise RuntimeError("Database not connected!")

        if (config := await GuildConfiguration.get(db, identifier)) is not None:
            # If a configuration was already in the database, return it.
            return config

        # Otherwise, create a new one, write it to the database and return that instead.
        config = GuildConfiguration.new(identifier)
        await config.write(db)
        return config

    @classmethod
    def new(cls, identifier: int) -> "GuildConfiguration":
        """Creates a new instance of `GuildConfiguration` for a guild with ID `identifier`."""
        return cls(
            guild_id=identifier,
            starboard_threshold=3,
            starboard_channel_id=None,
            starboard_emoji_id=None,
            who_asked_enabled=False,
            message_resender_enabled=False,
            starboard_enabled=False
        )

    @classmethod
    async def get(cls, db: motor_asyncio.AsyncIOMotorDatabase, identifier: int) -> t.Optional["GuildConfiguration"]:
        """Get the GuildConfiguration instance for a guild from the database. Returns `None` if the guild is not in the database."""
        collection = db["guild_settings"]
        query = {"guild_id": identifier}
        document = await collection.find_one(query, {"_id": False})

        if document is None:
            return None

        return cls(**document)

    async def write(self, db: motor_asyncio.AsyncIOMotorDatabase) -> None:
        """Writes the guild's configuration to the database."""
        collection = db["guild_settings"]
        query = {"guild_id": self.guild_id}
        document = dataclasses.asdict(self)
        await collection.replace_one(query, document, upsert=True)

    def starboard_ready(self) -> bool:
        """Checks whether this guild has its starboard configuration set."""
        members = (self.starboard_channel_id, self.starboard_emoji_id)
        return self.starboard_enabled == True and None not in members
