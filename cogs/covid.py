import discord.ext.commands as commands
import libs.utilities as utilities
import discord.ext.tasks as tasks
import libs.covid as covid
import datetime
import discord
import asyncio
import model
import re

class Covid(commands.Cog):
    """Daily COVID-19 tracker for New South Wales."""
    def __init__(self, bot: model.Bakerbot, backend: covid.Backend) -> None:
        self.backend = backend
        self.bot = bot

        # Start the statistics task if this channel exists in the bot's list.
        if (channel := bot.get_channel(473426067823263753)) is not None:
            self.covid_task.start(channel)

    def cog_unload(self):
        """Handles task cancellation on cog unload."""
        self.covid_task.cancel()

    def covid_embed(self, results: dict) -> discord.Embed:
        """Creates and returns a COVID-19 statistics embed."""
        time = datetime.datetime.utcnow().strftime("%A, %d %B %Y")

        embed = discord.Embed(colour=utilities.Colours.regular, timestamp=discord.utils.utcnow())
        footer = "Data taken from the NSW Data Analytics Centre."
        embed.set_footer(text=footer, icon_url=utilities.Icons.info)
        embed.title = f"COVID-19 Statistics as of {time}:"

        for key, value in results["data"][0].items():
            words = re.findall("[A-Z][^A-Z]*", key)
            embed.add_field(name=" ".join(words), value=f"{value:,}")

        return embed

    @tasks.loop(hours=24)
    async def covid_task(self, channel: discord.TextChannel) -> None:
        """Asynchronous task for displaying statistics every 24 hours."""
        now = datetime.datetime.now()
        execat = datetime.time(20, 30)
        delay = datetime.datetime.combine(now, execat)

        if (delay - now).days < 0:
            extra = datetime.timedelta(days=1)
            delay = datetime.datetime.combine(now + extra, execat)

        # Sleep until 8:30pm.
        seconds = (delay - now).total_seconds()
        await asyncio.sleep(seconds)

        results = await self.backend.request("datafiles/statsLocations.json")
        embed = self.covid_embed(results)
        await channel.send(embed=embed)

    @commands.command()
    async def covid(self, ctx: commands.Context) -> None:
        """Query the API for COVID-19 statistics in New South Wales."""
        results = await self.backend.request("datafiles/statsLocations.json")
        embed = self.covid_embed(results)
        await ctx.reply(embed=embed)

def setup(bot: model.Bakerbot) -> None:
    backend = covid.Backend(bot.session)
    cog = Covid(bot, backend)
    bot.add_cog(cog)
