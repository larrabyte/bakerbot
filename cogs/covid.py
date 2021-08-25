import backend.utilities as utilities
import backend.covid as covid
import model

import discord.ext.commands as commands
import discord.ext.tasks as tasks
import datetime
import discord
import asyncio

class Covid(commands.Cog):
    """Daily COVID-19 tracker for New South Wales."""
    def __init__(self, bot: model.Bakerbot, backend: covid.Backend) -> None:
        self.backend = backend
        self.bot = bot

        # Start the statistics task if this channel exists in the bot's list.
        if (channel := bot.get_channel(473426067823263753)) is not None:
            self.task.start(channel)

    def cog_unload(self):
        """Handles task cancellation on cog unload."""
        self.task.cancel()

    def embeddify(self, results: covid.Statistics) -> discord.Embed:
        """Creates and returns a COVID-19 statistics embed."""
        time = datetime.datetime.utcnow().strftime("%A, %d %B %Y")
        embed = utilities.Embeds.standard(title=f"COVID-19 Statistics as of {time}")
        embed.set_footer(text="Data taken from the NSW Data Analytics Centre.", icon_url=utilities.Icons.info)

        acquisitions = f"With a total of **{results.new:,}** cases:\n"
        acquisitions += f"* **{results.local:,}** cases were acquired locally.\n"
        acquisitions += f"* **{results.interstate:,}** cases were acquired interstate.\n"
        acquisitions += f"* **{results.overseas:,}** cases were acquired overseas."
        embed.add_field(name="New Acquisitions", value=acquisitions)

        totals = f"* **{results.tested:,}** tests have been administered.\n"
        totals += f"* **{results.cases:,}** cases have been recorded.\n"
        totals += f"* **{results.recovered:,}** people have recovered.\n"
        totals += f"* **{results.deaths:,}** deaths have been recorded."
        embed.add_field(name="Current State Totals", value=totals)
        return embed

    @tasks.loop(hours=24)
    async def task(self, channel: discord.TextChannel) -> None:
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

        results = await self.backend.statistics()
        embed = self.embeddify(results)
        await channel.send(embed=embed)

    @commands.command()
    async def covid(self, ctx: commands.Context) -> None:
        """Query the API for COVID-19 statistics in New South Wales."""
        results = await self.backend.statistics()
        embed = self.embeddify(results)
        await ctx.reply(embed=embed)

def setup(bot: model.Bakerbot) -> None:
    backend = covid.Backend(bot.session)
    cog = Covid(bot, backend)
    bot.add_cog(cog)
