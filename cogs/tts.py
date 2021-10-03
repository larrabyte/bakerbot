import backends.fifteen as fifteen
import utilities
import model

from discord.ext import commands
import typing as t
import collections
import discord
import asyncio
import re

class TTSFlags(commands.FlagConverter):
    """An object containing the parameters required to execute a FifteenAPI request."""
    voice: t.Optional[str]
    text: t.Optional[str]

class TTS(commands.Cog):
    """Text-to-speech using FifteenAI."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot
        self.lock = asyncio.Lock()
        self.queues = {}

    def queue(self, guild: discord.Guild) -> collections.deque:
        """Returns the guild's TTS queue."""
        if guild.id not in self.queues:
            self.queues[guild.id] = collections.deque()

        return self.queues[guild.id]

    def callback(self, client: discord.VoiceClient, queue: collections.deque) -> None:
        """Handles callbacks after the voice client finishes playing."""
        if not client.is_connected():
            queue.clear()
        elif len(queue) > 0:
            now = queue.popleft()
            client.play(now, after=lambda e: self.callback(client, queue))

    async def generator(self, voice: str, text: str) -> discord.FFmpegOpusAudio:
        """API request routine, called multiple times over different `text` inputs."""
        url = await fifteen.Backend.generate(voice, text)
        codec, bitrate = await discord.FFmpegOpusAudio.probe(url)

        options = {
            "codec": codec,
            "bitrate": bitrate if bitrate <= 512 else 512,
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn"
        }

        return discord.FFmpegOpusAudio(url, **options)

    @commands.command()
    async def tts(self, ctx: commands.Context, *, flags: TTSFlags) -> None:
        """Text-to-speech with a dash of machine learning."""
        if all(v is None for k, v in flags):
            tutorial = (f"Invoke text-to-speech like so: `$tts voice: <model name> text: <text>`\n"
                         "The voice flag is optional and defaults to The Narrator.")

            return await ctx.reply(tutorial)

        if ctx.voice_client is None and ctx.author.voice is not None and ctx.author.voice.channel is None:
            fail = utilities.Embeds.status(False)
            fail.description = "Unable to join a voice channel."
            fail.set_footer(text="Either the bot isn't in a channel or you aren't in one.", icon_url=utilities.Icons.CROSS)
            return await ctx.reply(embed=fail)

        flags.voice = flags.voice or "The Narrator"

        # Chunk the text into 200-character pieces and send a seperate API request for each one.
        async with ctx.typing():
            chunks = [flags.text[i:i + 200] for i in range(0, len(flags.text), 200)]
            coroutines = [self.generator(flags.voice, chunk) for chunk in chunks]
            results = await asyncio.gather(*coroutines)

        queue = self.queue(ctx.guild)
        async with self.lock:
            queue.extend(results)

        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            await ctx.author.voice.channel.connect()

        if not ctx.voice_client.is_playing():
            self.callback(ctx.voice_client, queue)
            await ctx.reply(f"Text-to-speech synthesis complete.")
        else:
            await ctx.reply(f"Text-to-speech audio received and placed in queue. You are #{len(queue)}.")

def setup(bot: model.Bakerbot) -> None:
    cog = TTS(bot)
    bot.add_cog(cog)
