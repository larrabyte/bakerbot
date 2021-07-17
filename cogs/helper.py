import discord.ext.commands as commands
import typing as t
import discord
import model

class Helper(commands.Cog):
    """Bakerbot's documentation lives here."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.colours = bot.utils.Colours
        self.icons = bot.utils.Icons
        self.embeds = bot.utils.Embeds
        self.bot = bot

    def cog_help(self, cogname: str) -> discord.Embed:
        """Returns the documentation for a specific cog."""
        if (cog := self.bot.get_cog(cogname.capitalize())) is None:
            fail = self.embeds.status(False, f"Could not find the `{cogname}` cog.")
            return fail

        embed = discord.Embed(colour=self.colours.regular, timestamp=self.embeds.now())
        footer = "Arguments enclosed in <> are required while [] are optional."
        embed.set_footer(text=footer, icon_url=self.icons.info)

        for command in cog.walk_commands():
            # We don't want group parent commands listed, ignore those.
            if isinstance(command, commands.Group): continue
            prefix = f"{command.full_parent_name}" if command.parent else ""
            embed.add_field(name=f"{prefix} {command.name} {command.signature}", value=command.help, inline=False)

        return embed

    def general_help(self) -> discord.Embed:
        """Returns documentation for Bakerbot."""
        embed = discord.Embed(colour=self.colours.regular, timestamp=self.embeds.now())
        footer = "Typing $help [cogname] will display commands in that cog."
        embed.set_footer(text=footer, icon_url=self.icons.info)

        # Get list of cog objects using self.bot.cogs and add fields to embed.
        for cog in [self.bot.cogs[name] for name in self.bot.cogs]:
            embed.add_field(name=cog.qualified_name.lower(), value=cog.description, inline=False)

        return embed

    @commands.command()
    async def help(self, ctx: commands.Context, cogname: t.Optional[str]) -> None:
        """Displays a list of cogs. Passing in `cogname` will display commands inside that cog."""
        embed = self.general_help() if cogname is None else self.cog_help(cogname)
        await ctx.reply(embed=embed)

def setup(bot: model.Bakerbot) -> None:
    cog = Helper(bot)
    bot.add_cog(cog)
