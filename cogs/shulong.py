import discord.ext.commands as commands
import typing as t
import discord
import random
import model

class Shulong(commands.Cog):
    """You can find scrumptious ideas from Shulong here."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    @commands.group(invoke_without_subcommand=True)
    async def shulong(self, ctx: commands.Context) -> None:
        """The parent command for all things Shulong related."""
        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                # There is no subcommand: inform the user about Shulong commands.
                summary = """Hi! Welcome to the Shulong command group.
                            This cog houses commands that are scrumptious (his words).
                            See `$help shulong` for a full list of available subcommands."""

                embed = discord.Embed(colour=self.colours.regular, timestamp=self.embeds.now())
                embed.set_footer(text="Powered by sheer stupidity.", icon_url=self.icons.info)
                embed.description = summary
                await ctx.reply(embed=embed)
            else:
                # The subcommand was not valid: throw a fit.
                command = f"${ctx.command.name} {ctx.subcommand_passed}"
                summary = f"`{command}` is not a valid command."
                footer = "Try $help shulong for a full list of available subcommands."
                embed = self.embeds.status(False, summary)
                embed.set_footer(text=footer, icon_url=self.icons.cross)
                await ctx.reply(embed=embed)

    @shulong.command()
    async def random(self, ctx: commands.Context) -> None:
        """Generates and returns a random unicode code point in the CJK range."""
        codepoint = random.randint(0x4E00, 0x9FFF)
        character = chr(codepoint)
        await ctx.reply(character)

    @shulong.command()
    async def dyslexify(self, ctx: commands.Context, category: t.Optional[discord.CategoryChannel]) -> None:
        """Turns server layouts into mush. Surprisingly, doesn't leave logs behind!"""
        categories = [category] if category is not None else ctx.guild.categories

        for group in categories:
            outside = random.randint(0, len(categories))
            await group.move(beginning=True, offset=outside)

            for channel in group.channels:
                inside = random.randint(0, len(ctx.guild.categories))
                await channel.move(beginning=True, offset=inside)

        await ctx.reply("Swag!")

def setup(bot: model.Bakerbot) -> None:
    cog = Shulong(bot)
    bot.add_cog(cog)
