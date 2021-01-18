from libs.utilities import Embeds, Colours, Icons

from discord.ext import commands
import typing as t
import discord

class Helper(commands.Cog):
    """Bakerbot's documentation lives here."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def help(self, ctx: commands.Context, cogname: t.Optional[str]) -> None:
        """Displays a list of cogs. Passing in `cogname` will display commands inside that cog."""
        if cogname is None:
            embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
            embed.set_footer(text="Typing $help [cogname] will display commands in that cog.", icon_url=Icons.info)

            # Get list of cog objects using self.bot.cogs and add fields to embed.
            for cog in [self.bot.cogs[name] for name in self.bot.cogs]:
                embed.add_field(name=cog.qualified_name.lower(), value=cog.description, inline=False)

            await ctx.send(embed=embed)
        else:
            # Attempt to get the cog object using self.bot.get_cog().
            if (cog := self.bot.get_cog(cogname.capitalize())) is not None:
                embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
                embed.set_footer(text="Arguments enclosed in <> are required while [] are optional.", icon_url=Icons.info)

                for command in cog.walk_commands():
                    # We don't want group parent commands listed, ignore those.
                    if isinstance(command, commands.Group): continue
                    prefix = f"{command.full_parent_name}" if command.parent else ""
                    embed.add_field(name=f"{prefix} {command.name} {command.signature}", value=command.help, inline=False)

                await ctx.send(embed=embed)
            else:
                # Welp, no cog found. Send an error.
                fail = Embeds.status(success=False, desc=f"Could not find the `{cogname}` cog.")
                await ctx.send(embed=fail)

def setup(bot): bot.add_cog(Helper(bot))
