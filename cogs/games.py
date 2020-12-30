from discord.ext import commands
import datetime as dt
import discord
import asyncio
import random

class GameError(commands.CommandError):
    GIVEAWAY_IN_PROGRESS = (0, "Giveaway currently in progress, please wait.")

    def __init__(self, error: tuple) -> None: self.error = error
    def __str__(self) -> str: return f"GameError({self.error[0]}) raised: {self.error[1]}"

class Games(commands.Cog, name="games"):
    """Bakerbot Twitch streaming coming soon, I promise!"""
    def __init__(self, bot: commands.Bot) -> None:
        bot.loop.create_task(self.startup())
        self.giving = False
        self.bot = bot

    async def startup(self) -> None:
        """Manages any cog prerequisites."""
        await self.bot.wait_until_ready()
        self.util = self.bot.get_cog("utilities")

    def game_embed(self, title: str) -> discord.Embed:
        """Returns a Discord Embed, useful for game-related commands."""
        embed = discord.Embed(title=title,
                              colour=self.util.gaming_colour,
                              timestamp=dt.datetime.utcnow())

        embed.set_footer("sponsored by omega pharma", icon_url=self.util.illuminati)
        return embed

    @commands.command()
    async def giveaway(self, ctx: commands.Context, *, prize: str) -> None:
        """Giveaway random prizes! Pass in a prize to display."""
        if self.giving: raise GameError(GameError.GIVEAWAY_IN_PROGRESS)
        self.giving = True

        size = 5 if len(ctx.guild.members) >= 5 else len(ctx.guild.members)
        members = random.sample(ctx.guild.members, size)
        displayed = "\n".join([member.mention for member in members])
        winner = random.choice(members)

        embed = self.game_embed(title=f"Bakerbot: {ctx.author.name}'s lottery!")
        embed.add_field(name="The Winner's Prize", value=prize, inline=False)
        embed.add_field(name="Potential Winners", value=displayed, inline=False)
        await ctx.send(embed=embed)

        await asyncio.sleep(random.randint(1, 10))
        embed = self.game_embed(title=f"Bakerbot: {ctx.author.name}'s lottery!")
        embed.add_field(name="code is fucked and so is ur mum :point_right: :sunglasses: :point_right:",
                        value=f"{winner.mention} wins {prize}!",
                        inline=False)

        await ctx.send(embed=embed)
        self.giving = False

def setup(bot): bot.add_cog(Games(bot))
