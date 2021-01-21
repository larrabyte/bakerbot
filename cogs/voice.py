from libs.utilities import Embeds, Colours, Icons, Regexes, Choices
from libs.audio import Nodes, Player, Action, RepeatMode
from libs.models import Bakerbot
from discord.ext import commands

import logging as log
import typing as t
import wavelink
import discord
import asyncio

class Voice(commands.Cog, wavelink.WavelinkMixin):
    """Controls the voice client for Bakerbot. Audio commands can be found here."""
    def __init__(self, bot: Bakerbot) -> None:
        self.bot = bot
        self.bot.loop.create_task(self.cog_setup())

    def cog_unload(self) -> None:
        # Destroy any active players before reloading.
        for player in self.bot.wavelink.players.values():
            self.bot.loop.create_task(player.destroy())

    @staticmethod
    def get_formatted_length(milliseconds: int, fixed: bool) -> t.Tuple[int]:
        # Get a formatted time string as a tuple of (minutes, seconds).
        minutes = str(int(milliseconds // (1000 * 60)))
        seconds = str(int((milliseconds // 1000) % 60))
        return (minutes, seconds.zfill(2) if fixed else seconds)

    def get_player(self, guild: discord.Guild) -> Player:
        # Returns the guild's associated player.
        return self.bot.wavelink.get_player(guild.id, cls=Player)

    async def cog_setup(self) -> None:
        # Setup the Wavelink nodes.
        for node in Nodes.dictionary.values():
            await self.bot.wavelink.initiate_node(**node)

    async def cog_check(self, ctx: commands.Context) -> None:
        # Cog check ensures that voice commands can't be executed in DMs.
        if isinstance(ctx.channel, discord.DMChannel):
            fail = Embeds.status(sucess=False, desc="Voice commands are unavailable inside DMs.")
            await ctx.send(embed=fail)
            return False

        return True

    async def get_tracks(self, query: str, search: bool, single: bool) -> t.Union[list, wavelink.Track, None]:
        # Wraps around self.bot.wavelink.get_tracks() for searches/direct URLs.
        results = await self.bot.wavelink.get_tracks(f"ytsearch:{query}" if search else query)
        if results is None:
            return None

        if isinstance(results, wavelink.TrackPlaylist):
            return results.tracks

        if single: return results[0]
        return list(results)

    @commands.command()
    async def play(self, ctx: commands.Context, *, query: t.Optional[str]) -> None:
        """Play some tunes! Also works as the resume command."""
        if query is None:
            # Maybe the user didn't know to pass in a query?
            embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
            embed.description = "No query passed in. Try passing in something: `$play arabic music`"
            embed.set_footer(text="See $help voice for more commands.", icon_url=Icons.info)
            return await ctx.send(embed=embed)

        query = query.strip("<>")
        search = not Regexes.url(query)
        if (result := await self.get_tracks(query, search, True)) is not None:
            # Ensure that we're connected before playing.
            player = self.get_player(ctx.guild)
            await ctx.invoke(self.connect, channel=None)
            if not player.is_connected: return

            embed = discord.Embed(title="Now queued." if player.is_playing else "Now playing.",
                                description=f"[{result.title}]({result.uri})",
                                colour=Colours.regular,
                                timestamp=Embeds.now())

            m, s = self.get_formatted_length(result.length, False)
            embed.set_footer(text=f"Track goes for {m} minutes and {s} seconds.", icon_url=ctx.author.avatar_url)
            if result.thumb is not None: embed.set_thumbnail(url=result.thumb)
            await ctx.send(embed=embed)

            player.queue.add_tracks(result)
            if not player.is_playing: await player.playback()
        else:
            fail = Embeds.status(success=False, desc="Failed to find any results.")
            await ctx.send(embed=fail)

    @commands.command()
    async def search(self, ctx: commands.Context, *, query: t.Optional[str]) -> None:
        """Search for your favourite tunes on YouTube."""
        if query is None:
            # Maybe the user didn't know to pass in a query?
            embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
            embed.description = "No query passed in. Try passing in something: `$search arabic music`"
            embed.set_footer(text="See $help voice for more commands.", icon_url=Icons.info)
            return await ctx.send(embed=embed)

        if (results := await self.get_tracks(query, True, False)) is not None:
            # Ensure that we're connected before playing.
            await ctx.invoke(self.connect, channel=None)
            player = self.get_player(ctx.guild)
            if not player.is_connected: return

            embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
            embed.set_footer(text=f"Showing 5/{len(results)} results.", icon_url=ctx.author.avatar_url)
            embed.description = ""
            results = results[:5]

            for index, track in enumerate(results):
                m, s = self.get_formatted_length(track.length, True)
                embed.description += f"**{index + 1}**. [{track.title}]({track.uri}) ({m}:{s})\n"

            # Get a integer selection using Choice.prompt().
            choice = await Choices.prompt(ctx=ctx, embed=embed, n=5, author_only=True)
            if choice is None: return await ctx.invoke(self.disconnect)

            embed = discord.Embed(title="Now queued." if player.is_playing else "Now playing.",
                                  description=f"[{results[choice].title}]({results[choice].uri})",
                                  colour=Colours.regular,
                                  timestamp=Embeds.now())

            m, s = self.get_formatted_length(results[choice].length, False)
            embed.set_footer(text=f"Track goes for {m} minutes and {s} seconds.", icon_url=ctx.author.avatar_url)
            if results[choice].thumb is not None: embed.set_thumbnail(url=results[choice].thumb)
            await ctx.send(embed=embed)

            player.queue.add_tracks(results[choice])
            if not player.is_playing: await player.playback()
        else:
            fail = Embeds.status(success=False, desc="Failed to find any results.")
            await ctx.send(embed=fail)

    @commands.command()
    async def queue(self, ctx: commands.Context) -> None:
        """Check out the current audio queue."""
        player = self.get_player(ctx.guild)

        if player.queue.empty:
            # The queue is empty. Send an embed to the user to let them know.
            embed = discord.Embed(description="Queue is currently empty.", colour=Colours.regular, timestamp=Embeds.now())
            embed.set_footer(text="Try playing some tracks!", icon_url=ctx.author.avatar_url)
            return await ctx.send(embed=embed)

        embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
        embed.set_footer(text=f"Current repeat mode: {player.queue.repeating.name}.", icon_url=ctx.author.avatar_url)

        # Add a history field if we have tracks in the queue history.
        if player.queue.history and (text := "") is not None:
            for index, track in enumerate(player.queue.history):
                text += f"**{index + 1}**. [{track.title}]({track.uri})\n"

            embed.add_field(name="Queue history:", value=text, inline=False)

            # Add an upcoming field if we have tracks ahead.
        if player.queue.upcoming and (text := "") is not None:
            for index, track in enumerate(player.queue.upcoming):
                text += f"**{index + 1}**. [{track.title}]({track.uri})\n"

            embed.add_field(name="Upcoming tracks:", value=text, inline=False)

        # Add the current track's field and its current status.
        if (current := player.queue.current_track) is not None:
            if not player.is_paused:
                em, es = self.get_formatted_length(player.position, True)
                tm, ts = self.get_formatted_length(current.length, True)
                if current.is_stream: title = f"Currently streaming: ```[{em}:{es}]```"
                else: title = f"Currently playing: ```[{em}:{es} / {tm}:{ts}]```"
            else: title = "Currently paused."

        embed.add_field(name=title, value=f"[{current.title}]({current.uri})", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def repeat(self, ctx: commands.Context, mode: t.Optional[str]) -> None:
        """Query or change the current repeat mode."""
        player = self.get_player(ctx.guild)

        # Show a helpful embed if an invalid mode was passed.
        if mode not in ["none", "one", "all"]:
            embed = discord.Embed(colours=Colours.regular, timestamp=Embeds.now())
            embed.description = "Valid repeat modes are: `none`, `one` and `all`."
            embed.set_footer(text=f"The current repeat mode is {player.queue.repeating.name}.", icon_url=Icons.info)
            return await ctx.send(embed=embed)

        # Otherwise, just set the mode and display a success message.
        if mode == "none": player.queue.repeating = RepeatMode.none
        elif mode == "one": player.queue.repeating = RepeatMode.one
        elif mode == "all": player.queue.repeating = RepeatMode.all

        embed = Embeds.status(success=True, desc=f"Changed repeat mode to `{mode}`.")
        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx: commands.Context) -> None:
        """Skip to the next track."""
        player = self.get_player(ctx.guild)

        # Don't even try if we're not connected.
        if not player.is_connected:
            fail = Embeds.status(success=False, desc="I'm not even connected. 😪")
            return await ctx.send(embed=fail)

        # Handle all the track calculations using futuretrack().
        player.action = Action.skip
        if (track := player.futuretrack()) is not None:
            embed = discord.Embed(title="Skipping to next track.",
                                  description=f"[{track.title}]({track.uri})",
                                  colour=Colours.regular,
                                  timestamp=Embeds.now())

            m, s = self.get_formatted_length(track.length, False)
            embed.set_footer(text=f"Track goes for {m} minutes and {s} seconds.", icon_url=ctx.author.avatar_url)
            if track.thumb is not None: embed.set_thumbnail(url=track.thumb)
            await ctx.send(embed=embed)

            # Use the Wavelink listener to advance if the bot is playing audio.
            if player.is_playing: await player.stop()
            else: await player.advance()
        else:
            fail = Embeds.status(success=False, desc="No tracks to skip to!")
            await ctx.send(embed=fail)

    @commands.command()
    async def rewind(self, ctx: commands.Context) -> None:
        """Rewind to the previous track."""
        player = self.get_player(ctx.guild)

        # Don't even try if we're not connected.
        if not player.is_connected:
            fail = Embeds.status(success=False, desc="I'm not even connected. 😪")
            return await ctx.send(embed=fail)

        # Handle all the track calculations using futuretrack().
        player.action = Action.rewind
        if (track := player.futuretrack()) is not None:
            embed = discord.Embed(title="Rewinding to previous track.",
                                  description=f"[{track.title}]({track.uri})",
                                  colour=Colours.regular,
                                  timestamp=Embeds.now())

            m, s = self.get_formatted_length(track.length, False)
            embed.set_footer(text=f"Track goes for {m} minutes and {s} seconds.", icon_url=ctx.author.avatar_url)
            if track.thumb is not None: embed.set_thumbnail(url=track.thumb)
            await ctx.send(embed=embed)

            # Use the Wavelink listener to advance if the bot is playing audio.
            if player.is_playing: await player.stop()
            else: await player.advance()
        else:
            fail = Embeds.status(success=False, desc="No tracks to rewind to!")
            await ctx.send(embed=fail)

    @commands.command()
    async def stop(self, ctx: commands.Context) -> None:
        """Stops playback and clears the audio queue."""
        player = self.get_player(ctx.guild)

        if not player.queue.empty:
            await player.stop()
            player.queue.clear_queue()
            embed = Embeds.status(success=True, desc="Playback stopped and queue cleared.")
            await ctx.send(embed=embed)

    @commands.command()
    async def connect(self, ctx: commands.Context, *, channel: t.Optional[discord.VoiceChannel]) -> None:
        """Connects to `channel` or the user's voice channel."""
        # We prioritise user-specified channels if they are available, else we use the author's current channel.
        destination = channel if channel is not None else getattr(ctx.author.voice, "channel", None)

        if destination is not None:
            player = self.get_player(ctx.guild)
            await player.connect(destination.id)
        else:
            fail = Embeds.status(success=False, desc=None)
            items = ctx.message.content.split()[1:]

            # Check that the user is invoking the connect command with an invalid channel.
            if len(items) > 0 and ctx.command.qualified_name == "connect":
                fail.description = f"`{' '.join(items)}` is not a valid voice channel."
            else:
                fail.description = "You aren't connected to a voice channel!"

            await ctx.send(embed=fail)

    @commands.command()
    async def disconnect(self, ctx: commands.Context) -> None:
        """Disconnects Bakerbot from a connected voice channel."""
        player = self.get_player(ctx.guild)

        if player.is_connected:
            if player.is_playing: await player.stop()
            await player.disconnect()
            player.queue.clear_queue()
        else:
            fail = Embeds.status(success=False, desc="I'm not even connected. 😪")
            await ctx.send(embed=fail)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # Called when someone leaves or joins the voice channel.
        if not member.bot and after.channel is None:
            if not [member for member in before.channel.members if not member.bot]:
                player = self.get_player(member.guild)
                if not player.is_paused: await player.set_pause(True)
        else:
            player = self.get_player(member.guild)
            if after.channel is not None and after.channel.id == player.channel_id:
                if player.is_paused:
                    await asyncio.sleep(0.5)
                    await player.set_pause(False)

    @wavelink.WavelinkMixin.listener()
    async def on_track_end(self, node: wavelink.Node, payload: wavelink.events.TrackEnd):
        # Called when Lavalink ends a track. We use it to advance the player.
        await payload.player.advance()

    @wavelink.WavelinkMixin.listener()
    async def on_track_stuck(self, node: wavelink.Node, payload: wavelink.events.TrackStuck):
        # Called when Lavalink gets stuck on a track. We use it to log the exception.
        log.error(f"PLAYER | Track got stuck at {payload.threshold}ms.")

    @wavelink.WavelinkMixin.listener()
    async def on_track_exception(self, node: wavelink.Node, payload: wavelink.events.TrackException):
        # Called when Lavalink encounters an exception. We use it to log the exception.
        log.error(f"PLAYER | Track exception: {payload.error}")

def setup(bot): bot.add_cog(Voice(bot))
