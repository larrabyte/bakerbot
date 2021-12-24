import utilities
import model

from discord.ext import commands
import discord
import typing

class Helper(commands.Cog):
    """Bakerbot's documentation lives here."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    def embeddify(self, cog: commands.Cog) -> discord.Embed:
        """Transform command group documentation into the format of a Discord embed."""
        embed = utilities.Embeds.standard(description=cog.description)
        embed.title = f"Documentation for `{cog.__class__.__module__}`:"
        embed.set_footer(text="Arguments enclosed in <> are required while [] are optional.", icon_url=utilities.Icons.INFO)

        for command in cog.walk_commands():
            # We don't want group parent commands listed, ignore those.
            if isinstance(command, commands.Group):
                continue

            signature = utilities.Commands.signature(command)
            embed.add_field(name=signature, value=command.help)

        return embed

    @commands.command()
    async def help(self, ctx: commands.Context, cog: str | None) -> None:
        """Send Bakerbot's documentation in a neatly formatted message."""
        view = DocumentationView(self.bot.cogs, self.embeddify)

        if cog is None:
            instructions = "Use the dropbown menu below to see help for a specific command group."
            return await ctx.reply(instructions, view=view)

        sanitised = cog.lower()
        if sanitised.startswith(("cogs.", "local.")):
            sanitised = sanitised.split(".")[1]

        if (name := sanitised.capitalize()) not in self.bot.cogs:
            fail = utilities.Embeds.status(False)
            fail.description = f"`{sanitised}` is not a cog."
            fail.set_footer(text="Consider using the dropdown menu from $help instead.", icon_url=utilities.Icons.CROSS)
            await ctx.reply(embed=fail)
        else:
            cog = self.bot.cogs[name]
            embed = self.embeddify(cog)
            await ctx.reply(embed=embed, view=view)

class DocumentationView(utilities.View):
    """Provides a method of browsing command group documentation."""
    def __init__(self, cogs: dict[str, commands.Cog], formatter: typing.Callable, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        self.formatter = formatter
        self.cogs = cogs

        self.menu = discord.ui.Select(placeholder="Select any cog to view its commands.")
        self.menu.callback = self.cog_callback

        limits = utilities.Limits
        for name, cog in self.cogs.items():
            label = limits.limit(cog.__class__.__module__, limits.SELECT_LABEL)
            name = limits.limit(name, limits.SELECT_VALUE)
            description = limits.limit(cog.description, limits.SELECT_DESCRIPTION)
            self.menu.add_option(label=label, value=name, description=description)

        self.add_item(self.menu)

    async def cog_callback(self, interaction: discord.Interaction) -> None:
        """Handle cog selection requests from the Select Menu."""
        selection = self.menu.values[0]
        cog = self.cogs[selection]
        embed = self.formatter(cog)
        await interaction.response.edit_message(content=None, embed=embed)

def setup(bot: model.Bakerbot) -> None:
    cog = Helper(bot)
    bot.add_cog(cog)
