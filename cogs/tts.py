from backends import fifteen
import utilities
import model

from urllib.parse import quote_plus

from discord.ext import commands
import collections
import discord
import asyncio

class TTSFlags(commands.FlagConverter):
    """Parameters required to execute a FifteenAPI request."""
    voice: str | None
    text: str | None

class TTS(commands.Cog):
    """Text-to-speech using FifteenAI."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.lock = asyncio.Lock()
        self.queues = {}
        self.bot = bot

    def queue(self, guild: discord.Guild) -> collections.deque:
        """Return the guild's TTS queue."""
        if guild.id not in self.queues:
            self.queues[guild.id] = collections.deque()

        return self.queues[guild.id]

    def callback(self, client: discord.VoiceClient, queue: collections.deque) -> None:
        """Handle callbacks after the voice client finishes playing."""
        if not client.is_connected():
            queue.clear()
        elif len(queue) > 0:
            now = queue.popleft()
            client.play(now, after=lambda e: self.callback(client, queue))

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Ensure commands are being executed in a guild context."""
        return ctx.guild is not None

    async def generator(self, voice: str, text: str) -> discord.FFmpegOpusAudio:
        """API request routine: called multiple times over different `text` inputs."""
        url = await fifteen.Backend.generate(voice, text)
        codec, bitrate = await discord.FFmpegOpusAudio.probe(url)

        options = {
            "codec": codec,
            "bitrate": bitrate if bitrate is not None and bitrate <= 512 else 512,
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn"
        }

        return discord.FFmpegOpusAudio(url, **options)

    def make_sam_url(phrase: str):
        safe_url = f"https://tetyys.com/SAPI4/SAPI4?text={quote_plus(phrase)}&voice=Sam&pitch=100&speed=150"
        return discord.FFmpegPCMAudio(safe_url)


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

        async with ctx.typing():
            # Chunk the text into 200-character pieces and send a seperate API request for each one.
            chunks = (flags.text[i:i + 200] for i in range(0, len(flags.text), 200))
            coroutines = [self.generator(flags.voice, chunk) for chunk in chunks]

            try:
                results = await asyncio.gather(*coroutines)
            except fifteen.Unprocessable:
                fail = utilities.Embeds.status(False)
                fail.description = f"API refused to process your input."
                fail.set_footer(text="Maybe there are numbers in your text?", icon_url=utilities.Icons.CROSS)
                return await ctx.reply(embed=fail)

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
    
    @commands.command()
    async def sam(self, ctx: commands.Context, *, phrase: str ) -> None:
        """Its microsoft Sam, Y'all"""

        if ctx.voice_client is None and ctx.author.voice is not None and ctx.author.voice.channel is None:
            fail = utilities.Embeds.status(False)
            fail.description = "Unable to join a voice channel."
            fail.set_footer(text="Either the bot isn't in a channel or you aren't in one.", icon_url=utilities.Icons.CROSS)
            return await ctx.reply(embed=fail)

        sam_audio = self.make_sam_url(phrase)

        queue = self.queue(ctx.guild)
        async with self.lock:
            queue.append(sam_audio)

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
