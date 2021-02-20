from libs.utilities import Embeds, Colours
from libs.models import Bakerbot
from discord.ext import commands
from libs.jisho import Jisho

import discord

class Japan(commands.Cog):
    """Just Japanese Beginners things."""
    def __init__(self, bot: Bakerbot) -> None:
        self.bot = bot

    @commands.command()
    async def jisho(self, ctx: commands.Context, *, query: str) -> None:
        """Harness the power of Jisho (a Japanese dictionary)."""
        async with ctx.typing():
            if (response := await Jisho.search(query)) is None or not response:
                fail = Embeds.status(success=False, desc="Jisho couldn't find anything.")
                return await ctx.send(embed=fail)

        embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
        embed.set_footer(text="こんにちは！", icon_url=ctx.author.avatar_url)

        for word in response:
            description = f"{word.kana}\n" if word.kana != word.written else ""
            description += f"**{word.types}:** {word.definitions}"
            embed.add_field(name=f"{word.written}", value=description)

        await ctx.send(embed=embed)

def setup(bot): bot.add_cog(Japan(bot))
