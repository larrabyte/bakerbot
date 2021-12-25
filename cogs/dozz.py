import model
import asyncio
import ujson


from discord.ext import commands


class Loader(commands.Cog):
    """dominics fuckaround"""
            
    def __init__(self, bot: model.Bakerbot):
        self.bot = bot

    async def get_joke(self):
        """Get a fucking joke"""
        url = 'https://sv443.net/jokeapi/v2/'
        async with self.session.get(url) as response:
            data = await response.read()

            if response.status !=200:
                try: formatted = ujson.loads(data)
                except ValueError: formatted = {}
                error = str(formatted.get("errors", None))
                raise Exception(F"HTTP fuckup {response.status}: {error}")

            return ujson.loads(data)
    
    @commands.command()
    async def joke(self, ctx: commands.Context) -> None:
        """let see what the fuck happens."""
        async with ctx.typing():
            ctx.reply("OK, cooking up a joke.")
            joke = await self.get_joke()
            # if it failed, it throws exception by now.
            try:
                ctx.send(joke['setup'])
                await asyncio.sleep(5)
                ctx.send(joke['delivery'])
            except KeyError:
                # musn't be a
                ctx.send(joke['joke'])
            

def setup(bot: model.Bakerbot) -> None:
    cog = Loader(bot)
    bot.add_cog(cog)