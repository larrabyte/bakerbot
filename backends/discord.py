import exceptions
import model

from discord.ext import commands
import datetime as dt
import typing as t
import dataclasses
import discord
import aiohttp
import asyncio
import base64
import dacite
import ujson
import types
import http

class Gateway:
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_QUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11
    GUILD_SYNC = 12
    START_STREAM = 18
    DELETE_STREAM = 19

@dataclasses.dataclass
class HelloPayload:
    heartbeat_interval: int

    @classmethod
    def from_dict(cls, data: dict) -> "HelloPayload":
        return dacite.from_dict(cls, data)

@dataclasses.dataclass
class ReadyPayload:
    v: int
    users: t.Optional[t.Any]
    user_settings: t.Any
    user: t.Any
    tutorial: t.Optional[t.Any]
    session_id: str
    relationships: t.Any
    read_state: t.Any
    private_channels: t.Any
    merged_members: t.Optional[t.Any]
    guilds: t.Any
    guild_join_requests: t.Any
    guild_experiments: t.Any
    geo_ordered_rtc_regions: t.Any
    friend_suggestion_count: int
    experiments: t.Any
    country_code: str
    consents: t.Any
    connected_accounts: t.Any
    analytics_token: str

    @classmethod
    def from_dict(cls, data: dict) -> "ReadyPayload":
        return dacite.from_dict(cls, data)

@dataclasses.dataclass
class VoiceStateUpdatePayload:
    guild_id: t.Optional[str]
    channel_id: t.Optional[str]
    user_id: str
    member: t.Optional[t.Any]
    session_id: str
    deaf: bool
    mute: bool
    self_deaf: bool
    self_mute: bool
    self_stream: t.Optional[bool]
    self_video: bool
    suppress: bool
    request_to_speak_timestamp: t.Optional[dt.datetime]

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceStateUpdatePayload":
        config = dacite.Config({dt.datetime: dt.date.fromisoformat})
        return dacite.from_dict(cls, data, config)

@dataclasses.dataclass
class StreamCreatePayload:
    viewer_ids: t.Any
    stream_key: str
    rtc_server_id: str
    region: str
    paused: bool

    @classmethod
    def from_dict(cls, data: dict) -> "StreamCreatePayload":
        return dacite.from_dict(cls, data)

@dataclasses.dataclass
class VoiceServerUpdatePayload:
    token: str
    guild_id: str
    endpoint: t.Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceServerUpdatePayload":
        return dacite.from_dict(cls, data)

@dataclasses.dataclass
class StreamServerUpdatePayload:
    token: str
    stream_key: str
    guild_id: t.Optional[str]
    endpoint: str

    @classmethod
    def from_dict(cls, data: dict) -> "StreamServerUpdatePayload":
        return dacite.from_dict(cls, data)

@dataclasses.dataclass
class EventCallbackHandler:
    """Handles """
    payload_type: t.Type
    listeners: list = dataclasses.field(default_factory=list)
    waiters: list = dataclasses.field(default_factory=list)

@dataclasses.dataclass
class EventWaiter:
    future: asyncio.Future
    predicate: t.Callable
    event: str

class UDPConnectionState:
    def __init__(self) -> None:
        self.guild_id: t.Optional[int] = None
        self.channel_id: t.Optional[int] = None
        self.voice_token: t.Optional[str] = None
        self.voice_endpoint: t.Optional[str] = None
        self.stream_token: t.Optional[str] = None
        self.stream_key: t.Optional[str] = None
        self.stream_endpoint: t.Optional[str] = None
        self.stream_region: t.Optional[str] = None
        self.rtc_server_id: t.Optional[str] = None

class InfiniteWrapper:
    @staticmethod
    def create(coroutine: t.Coroutine, callback: t.Callable, interval: float) -> asyncio.Task:
        """Schedules `coroutine` for repeated execution every `interval` seconds."""
        wrapped = InfiniteWrapper.meat(coroutine, interval)
        task = asyncio.create_task(wrapped)
        task.add_done_callback(callback)
        return task

    @staticmethod
    async def meat(coroutine: t.Coroutine, interval: float) -> None:
        """Infinite wrapper implementation."""
        while True:
            await asyncio.sleep(interval)
            await coroutine()

class DiscordWebSocket:
    def __init__(self, ctx: commands.Context, ws: aiohttp.ClientWebSocketResponse, hello: HelloPayload) -> None:
        self.dispatch = {
            "READY": EventCallbackHandler(ReadyPayload),
            "VOICE_STATE_UPDATE": EventCallbackHandler(VoiceStateUpdatePayload),
            "STREAM_CREATE": EventCallbackHandler(StreamCreatePayload),
            "VOICE_SERVER_UPDATE": EventCallbackHandler(VoiceServerUpdatePayload),
            "STREAM_SERVER_UPDATE": EventCallbackHandler(StreamServerUpdatePayload)
        }

        self.heartbeater = InfiniteWrapper.create(self.heartbeat, self.callback, hello.heartbeat_interval / 1000.0)
        self.poller = InfiniteWrapper.create(self.poll, self.callback, 0.0)
        self.sequence = 0
        self.ctx = ctx
        self.ws = ws

    async def heartbeat(self) -> None:
        """Sends an Opcode 1 Heartbeat payload."""
        payload = {
            "op": Gateway.HEARTBEAT,
            "d": self.sequence
        }

        await self.ws.send_json(payload, dumps=ujson.dumps)

    async def identify(self, token: str) -> None:
        """Sends an Opcode 2 Identify payload."""
        payload = {
            "op": Gateway.IDENTIFY,
            "d": {
                "token": token,
                "properties": {
                    "os": "Linux",
                    "browser": "Firefox",
                    "device": ""
                }
            }
        }

        await self.ws.send_json(payload, dumps=ujson.dumps)

    async def voice_state_update(self, guild: int, channel: int, *, mute: bool=False, deaf: bool=False, video: bool=False) -> None:
        """Sends an Opcode 4 Voice State Update payload."""
        payload = {
            "op": Gateway.VOICE_STATE_UPDATE,
            "d": {
                "guild_id": guild,
                "channel_id": channel,
                "self_mute": mute,
                "self_deaf": deaf,
                "self_video": video
            }
        }

        await self.ws.send_json(payload, dumps=ujson.dumps)

    async def stream_create(self, guild: int, channel: int) -> None:
        """Sends an Opcode 18 Create Stream payload."""
        payload = {
            "op": Gateway.START_STREAM,
            "d": {
                "type": "guild",
                "guild_id": guild,
                "channel_id": channel,
                "preferred_region": None
            }
        }

        await self.ws.send_json(payload, dumps=ujson.dumps)

    def callback(self, future: asyncio.Future) -> None:
        """Called if any of our `InfiniteWrapper` tasks returns."""
        try:
            if (exception := future.exception()) is not None:
                for handler in self.dispatch.values():
                    for waiter in handler.waiters:
                        waiter.future.set_exception(exception)

        except asyncio.CancelledError:
            pass

    def add_listener(self, event: str, coroutine: t.Coroutine) -> None:
        """Adds a listener coroutine to the websocket."""
        if event not in self.dispatch:
            raise UnknownEvent

        handler = self.dispatch[event]
        handler.listeners.append(coroutine)

    async def wait_for(self, event: str, predicate: t.Callable=lambda p: True) -> asyncio.Future:
        """Awaits for an Opcode 0 Dispatch payload with a `t` value of `event`."""
        if event not in self.dispatch:
            raise UnknownEvent

        handler = self.dispatch[event]
        future = asyncio.get_running_loop().create_future()
        waiter = EventWaiter(future, predicate, event)
        handler.waiters.append(waiter)
        return await future

    async def poll(self) -> None:
        """Awaits for data from the websocket and dispatches it appropriately."""
        payload = await self.ws.receive_json(loads=ujson.loads)
        op, t, d = payload["op"], payload["t"], payload["d"]
        self.sequence = payload["s"] or self.sequence

        print(f"[bakerbot] gateway payload received (opcode {op}, event {t})")

        if op == Gateway.DISPATCH and t in self.dispatch:
            handler = self.dispatch[t]

            c = handler.payload_type.from_dict(d)
            for coroutine in handler.listeners:
                await coroutine(c)

            done_waiters = [waiter for waiter in handler.waiters if t == waiter.event and waiter.predicate(c)]
            handler.waiters = [waiter for waiter in handler.waiters if waiter not in done_waiters]
            for waiter in done_waiters:
                waiter.future.set_result(c)

        elif op == Gateway.HEARTBEAT:
            await self.heartbeat()

        elif op == Gateway.INVALID_SESSION:
            return await self.close(4444)

    async def close(self, code: int) -> None:
        """Cancels websocket-related tasks and closes the connection."""
        self.heartbeater.cancel()
        self.poller.cancel()
        await self.ws.close(code=code)

class User:
    """Represents a user in Discord."""
    lock = asyncio.Lock()

    def __init__(self, ctx: commands.Context, token: str, identifier: int) -> None:
        self.udp = UDPConnectionState()
        self.identifier = identifier
        self.token = token
        self.ctx = ctx

        # Assigned during asynchronous context entry.
        self.conn: t.Optional[DiscordWebSocket] = None
        self.session: t.Optional[str] = None

    async def __aenter__(self) -> "User":
        # Ensure there is only one instance active.
        await self.lock.acquire()

        gateway = await Backend.gateway()
        ws = await Backend.session.ws_connect(gateway)
        hello = await ws.receive_json(loads=ujson.loads)
        converted = HelloPayload.from_dict(hello["d"])
        self.conn = DiscordWebSocket(self.ctx, ws, converted)

        # Register event handlers before we start sending data.
        self.conn.add_listener("VOICE_STATE_UPDATE", self.on_voice_state_update)
        self.conn.add_listener("STREAM_CREATE", self.on_stream_create)
        self.conn.add_listener("VOICE_SERVER_UPDATE", self.on_voice_server_update)
        self.conn.add_listener("STREAM_SERVER_UPDATE", self.on_stream_server_update)

        await self.conn.identify(self.token)
        ready = await self.conn.wait_for("READY")
        self.session_id = ready.session_id

        return self

    async def __aexit__(self, typename: BaseException, exception: Exception, traceback: types.TracebackType) -> None:
        await self.conn.close(1000)
        self.lock.release()

    async def on_voice_state_update(self, payload: VoiceStateUpdatePayload) -> None:
        if int(payload.user_id) == self.identifier:
            self.udp.guild_id = None if not payload.guild_id else int(payload.guild_id)
            self.udp.channel_id = None if not payload.channel_id else int(payload.channel_id)

    async def on_stream_create(self, payload: StreamCreatePayload) -> None:
        self.udp.stream_key = payload.stream_key
        self.udp.rtc_server_id = payload.rtc_server_id
        self.udp.stream_region = payload.region

    async def on_voice_server_update(self, payload: VoiceServerUpdatePayload) -> None:
        self.udp.voice_token = payload.token
        self.udp.voice_endpoint = payload.endpoint

    async def on_stream_server_update(self, payload: StreamServerUpdatePayload) -> None:
        self.udp.stream_token = payload.token
        self.udp.stream_endpoint = payload.endpoint

    @staticmethod
    async def create_event(channel: discord.VoiceChannel, token: str, name: str, description: str, *, time: t.Optional[dt.datetime]=None) -> None:
        """Creates a Guild Event for `channel` with a name, description and optional time."""
        time = time or dt.datetime.utcnow() + dt.timedelta(seconds=5)

        payload = {
            "channel_id": channel.id,
            "description": description,
            "entity_metadata": None,
            "entity_type": 2,
            "name": name,
            "privacy_level": 2,
            "scheduled_start_time": time.isoformat()
        }

        properties = {
            "os": "Linux",
            "browser": "Firefox",
            "device": "",
            "system_locale": "en-AU",
            "browser_user_agent": "Mozilla/6.9 Gecko/20100101 Firefox/9001.0.0",
            "browser_version": "9001.0.0",
            "os_version": "5.0.0",
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": 100054,
            "client_event_source": None
        }

        properties = base64.b64encode(ujson.dumps(properties).encode("utf-8")).decode("utf-8")
        headers = {"Authorization": token, "X-Super-Properties": properties}
        await Backend.post(f"guilds/{channel.guild.id}/events", json=payload, headers=headers)

    async def connect(self, channel: discord.VoiceChannel) -> None:
        """Connects this user to a voice channel."""
        await self.conn.voice_state_update(channel.guild.id, channel.id)
        await self.conn.wait_for("VOICE_STATE_UPDATE", lambda p: int(p.user_id) == self.identifier)
        await self.conn.wait_for("VOICE_SERVER_UPDATE", lambda p: int(p.guild_id) == channel.guild.id)

    async def stream(self) -> None:
        """Starts a Go Live stream in the currently connected channel."""
        if self.udp is None or self.udp.guild_id is None or self.udp.channel_id is None:
            raise commands.ChannelNotFound("None")

        await self.conn.stream_create(self.udp.guild_id, self.udp.channel_id)
        await self.conn.wait_for("STREAM_CREATE")
        await self.conn.wait_for("VOICE_STATE_UPDATE", lambda p: int(p.user_id) == self.identifier)
        await self.conn.wait_for("STREAM_SERVER_UPDATE")

    async def disconnect(self) -> None:
        """Disconnects this user from any currently connected channels."""
        await self.conn.voice_state_update(None, None)
        await self.conn.wait_for("VOICE_STATE_UPDATE", lambda p: int(p.user_id) == self.identifier)

class Webhooks:
    @staticmethod
    async def create(channel: discord.TextChannel, name: str) -> None:
        """Creates a new webhook in `channel` with the name of `name`."""
        if Backend.token is None:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        headers = {"Authorization": f"Bot {Backend.token}"}
        payload = {"name": name}
        endpoint = f"channels/{channel.id}/webhooks"
        await Backend.post(endpoint, json=payload, headers=headers)

    @staticmethod
    async def move(webhook: discord.Webhook, channel: discord.TextChannel) -> None:
        """Moves `webhook` from its current channel to `channel`."""
        if Backend.token is None:
            raise exceptions.SecretNotFound("discord-token not specified in secrets.json.")

        headers = {"Authorization": f"Bot {Backend.token}"}
        payload = {"channel_id": channel.id}
        endpoint = f"webhooks/{webhook.id}"
        await Backend.post(endpoint, json=payload, headers=headers)

class Backend:
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        cls.base = "https://discord.com/api/v9"
        cls.session = bot.session
        cls.token = bot.secrets.get("discord-token", None)
        cls.gateway_url = ""

    @classmethod
    async def get(cls, endpoint: str, **kwargs: dict) -> dict:
        """Sends a HTTP GET request to the Discord API."""
        async with Backend.session.get(f"{Backend.base}/{endpoint}", **kwargs) as response:
            data = await response.json(encoding="utf-8", loads=ujson.loads)

            if response.status != http.HTTPStatus.OK:
                error = data.get("message", None)
                raise exceptions.HTTPUnexpected(response.status, error)

            return data

    @classmethod
    async def post(cls, endpoint: str, **kwargs: dict) -> dict:
        """Sends a HTTP POST request to the Discord API."""
        async with Backend.session.post(f"{Backend.base}/{endpoint}", **kwargs) as response:
            data = await response.json(encoding="utf-8", loads=ujson.loads)

            if response.status != http.HTTPStatus.OK:
                error = data.get("message", None)
                raise exceptions.HTTPUnexpected(response.status, error)

            return data

    @classmethod
    async def gateway(cls) -> str:
        """Returns a URL for connecting to a gateway."""
        if not cls.gateway_url:
            result = await cls.get("gateway")
            cls.gateway_url = result["url"]

        return cls.gateway_url + "/?v=9&encoding=json"

class UnknownEvent(Exception):
    """Raised when an unknown event is passed into `DiscordWebSocket.wait_for()`."""
    pass

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
