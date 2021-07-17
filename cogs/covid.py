import discord.ext.commands as commands
import discord.ext.tasks as tasks
import datetime
import discord
import asyncio
import model
import ujson
import yarl
import re

class Covid(commands.Cog):
    """Daily COVID-19 tracker for New South Wales."""
    def __init__(self, bot: model.Bakerbot, backend: "CovidBackend") -> None:
        self.colours = bot.utils.Colours
        self.icons = bot.utils.Icons
        self.embeds = bot.utils.Embeds
        self.backend = backend
        self.bot = bot

        # Start the statistics task.
        self.covid_task.start()

    def covid_embed(self, results: dict) -> discord.Embed:
        """Creates and returns a COVID-19 statistics embed."""
        time = datetime.datetime.utcnow().strftime("%A, %d %B %Y")

        embed = discord.Embed(colour=self.colours.regular, timestamp=self.embeds.now())
        footer = "Data taken from the NSW Data Analytics Centre."
        embed.set_footer(text=footer, icon_url=self.icons.info)
        embed.title = f"COVID-19 Statistics as of {time}:"

        for key, value in results["data"][0].items():
            words = re.findall("[A-Z][^A-Z]*", key)
            embed.add_field(name=" ".join(words), value=f"{value:,}")

        return embed

    @tasks.loop(hours=24)
    async def covid_task(self) -> None:
        """Asynchronous task for displaying statistics every 24 hours."""
        now = datetime.datetime.now()
        execat = datetime.time(20, 30)
        delay = datetime.datetime.combine(now, execat)
        delta = delay - now

        if delta.days < 0:
            extra = datetime.timedelta(days=1)
            delay = datetime.datetime.combine(now + extra, execat)

        # Sleep until 8:30pm.
        await asyncio.sleep(delta.total_seconds())

        channel = self.bot.get_channel(473426067823263753)
        results = await self.backend.request("datafiles/statsLocations.json")
        embed = self.covid_embed(results)
        await channel.send(embed=embed)

    @commands.command()
    async def covid(self, ctx: commands.Context) -> None:
        """Query the API for COVID-19 statistics in New South Wales."""
        results = await self.backend.request("datafiles/statsLocations.json")
        embed = self.covid_embed(results)
        await ctx.reply(embed=embed)

class CovidBackend:
    """Backend COVID-19 API wrapper."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.base = "https://nswdac-covid-19-postcode-heatmap.azurewebsites.net"
        self.session = bot.session

    async def request(self, path: str) -> dict:
        """Sends a HTTP GET request to the COVID-19 API."""
        url = yarl.URL(f"{self.base}/{path}")

        async with self.session.get(url) as resp:
            data = await resp.read()
            data = data.decode("utf-8")
            return ujson.loads(data)

def setup(bot: model.Bakerbot) -> None:
    backend = CovidBackend(bot)
    cog = Covid(bot, backend)
    bot.add_cog(cog)
