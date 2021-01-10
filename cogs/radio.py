from discord.ext import commands
import datetime as dt
import discord

class Radio(commands.Cog, name="radio"):
    """Internet radio streaming since 2020."""
    def __init__(self, bot: commands.Bot) -> None:
        bot.loop.create_task(self.startup())
        self.bot = bot

    async def startup(self) -> None:
        """Manages any cog prerequisites."""
        await self.bot.wait_until_ready()
        self.util = self.bot.get_cog("utilities")
        self.voice = self.bot.get_cog("voice")

    @commands.command()
    async def rfakhmer(self, ctx: commands.Context):
        """Radio Free Asia: Khmer language edition."""
        player = self.voice.get_player(ctx)
        if not player.is_connected: await player.connect(ctx)

        url = "https://www.youtube.com/playlist?list=PLegvw6u72Fag2mrW-_vQQZtz2YlpKJzpA"
        playlist = await self.voice.get_tracks(url, False)
        track = await self.voice.get_tracks(playlist[0].uri, False)
        track = track[0]

        embed = discord.Embed(title="Bakerbot: Radio Free Asia.",
                              description=f"[{track.title}]({track.uri})",
                              colour=self.util.regular_colour,
                              timestamp=dt.datetime.utcnow())

        footer = "Connected to a YouTube livestream." if track.is_stream else "Playing back a recorded stream."
        embed.set_footer(text=footer, icon_url=self.util.rfa_logo)
        await ctx.send(embed=embed)

        player.queue.clear_queue()
        await player.add_tracks(ctx, track)

def setup(bot): bot.add_cog(Radio(bot))
