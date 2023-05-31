import dataclasses
import datetime
import asyncpg
import typing

@dataclasses.dataclass
class GuildConfiguration:
    """A persistent guild-specific configuration."""
    guild_id: int
    starboard_reaction_threshold: int | None
    starboard_channel_id: int | None
    starboard_reaction_string: str | None

    def starboard_configured(self) -> bool:
        """Check if all starboard fields are valid."""
        return (
            self.starboard_reaction_threshold is not None and
            self.starboard_channel_id is not None and
            self.starboard_reaction_string is not None and
            self.starboard_reaction_threshold > 0
        )

    @classmethod
    async def read(cls, pool: asyncpg.Pool, id: int) -> "GuildConfiguration | None":
        """Read an instance of a guild configuration from the database."""
        async with pool.acquire() as connection, connection.transaction(readonly=True):
            query = "SELECT * FROM guild_settings WHERE guild_id = $1"
            response = typing.cast(asyncpg.Record | None, await connection.fetchrow(query, id))

            if response is None:
                return None

            return cls(**response)

    async def write(self, pool: asyncpg.Pool):
        """Write this instance to the database."""
        async with pool.acquire() as connection, connection.transaction():
            await connection.execute(
                "INSERT INTO guild_settings "
                "VALUES ($1, $2, $3, $4) "
                "ON CONFLICT (guild_id) "
                "DO UPDATE SET "
                "starboard_reaction_threshold = $2, "
                "starboard_channel_id = $3, "
                "starboard_reaction_string = $4;",
                self.guild_id,
                self.starboard_reaction_threshold,
                self.starboard_channel_id,
                self.starboard_reaction_string
            )

@dataclasses.dataclass
class StarboardMessage:
    """A persistent message."""
    message_id: int
    author_id: int
    channel_id: int
    guild_id: int
    reply_id: int | None
    timestamp: datetime.datetime
    content: str
    attachments: list[str]
    stickers: list[str]
    reactions: int

    @classmethod
    async def read(cls, pool: asyncpg.Pool, id: int) -> "StarboardMessage | None":
        """Read an instance of a starboard message from the database."""
        async with pool.acquire() as connection, connection.transaction(readonly=True):
            query = "SELECT * FROM starboard_messages WHERE message_id = $1"
            response = typing.cast(asyncpg.Record | None, await connection.fetchrow(query, id))

            if response is None:
                return None

            # We need to convert the record into a dictionary
            # in order to modify the attachment and sticker fields
            # to be lists instead of newline-separated strings.
            fields = dict(response)
            fields["attachments"] = fields["attachments"].split("\n")
            fields["stickers"] = fields["stickers"].split("\n")

            return cls(**fields)

    async def write(self, pool: asyncpg.Pool):
        """Write this instance to the database."""
        async with pool.acquire() as connection, connection.transaction():
            await connection.execute(
                "INSERT INTO starboard_messages "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) "
                "ON CONFLICT (message_id) "
                "DO UPDATE SET "
                "author_id = $2, "
                "channel_id = $3, "
                "guild_id = $4, "
                "reply_id = $5, "
                "timestamp = $6, "
                "content = $7, "
                "attachments = $8, "
                "stickers = $9, "
                "reactions = $10;",
                self.message_id,
                self.author_id,
                self.channel_id,
                self.guild_id,
                self.reply_id,
                self.timestamp,
                self.content,
                "\n".join(self.attachments),
                "\n".join(self.stickers),
                self.reactions
            )
