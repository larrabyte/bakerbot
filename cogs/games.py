import discord.ext.commands as commands
import libs.utilities as utilities
import libs.monopoly as monopoly
import discord
import asyncio
import model

class Games(commands.Cog):
    """Play a game with your friends through Bakerbot!"""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

        self.classes = {
            "monopoly": monopoly.Monopoly
        }

    @commands.group(invoke_without_subcommand=True)
    async def games(self, ctx: commands.Context) -> None:
        """The parent command for games on Bakerbot."""
        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                # There is no subcommand: inform the user about some games.
                summary = """Hi! Welcome to Bakerbot's gaming command group.
                            This cog houses swag and epic commands related to gaming.
                            See `$help games` for a full list of available subcommands."""

                embed = discord.Embed(colour=utilities.Colours.regular, timestamp=discord.utils.utcnow())
                embed.description = summary
                embed.set_footer(text="Powered by the Hugging Face API.", icon_url=utilities.Icons.info)
                await ctx.reply(embed=embed)
            else:
                # The subcommand was not valid: throw a fit.
                command = f"${ctx.command.name} {ctx.subcommand_passed}"
                summary = f"`{command}` is not a valid command."
                footer = "Try $help games for a full list of available subcommands."
                embed = utilities.Embeds.status(False, summary)
                embed.set_footer(text=footer, icon_url=utilities.Icons.cross)
                await ctx.reply(embed=embed)

    @games.command()
    async def play(self, ctx: commands.Context, *, game: str) -> None:
        """Would you like to play a game?"""
        if game.lower() not in self.classes:
            fail = utilities.Embeds.status(False, f"Game `{game}` not found!")
            return await ctx.reply(embed=fail)

        instance = self.classes[game]
        message = await ctx.reply("Please wait as the game is created...")
        await asyncio.sleep(0.5)
        await instance().run(message)

def setup(bot: model.Bakerbot) -> None:
    cog = Games(bot)
    bot.add_cog(cog)
