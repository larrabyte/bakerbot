import utilities
import model

import discord.ext.commands as commands
import typing as t
import discord

class Helper(commands.Cog):
    """Bakerbot's documentation lives here."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    def embeddify(self, cog: commands.Cog) -> discord.Embed:
        """Transforms command group documentation into the format of a Discord embed."""
        embed = utilities.Embeds.standard(description=cog.description)
        embed.title = f"Documentation for `{cog.__class__.__module__}`:"
        footer = "Arguments enclosed in <> are required while [] are optional."
        embed.set_footer(text=footer, icon_url=utilities.Icons.INFO)

        for command in cog.walk_commands():
            # We don't want group parent commands listed, ignore those.
            if isinstance(command, commands.Group):
                continue

            prefix = f"{command.full_parent_name} " if command.parent else ""
            signature = f"${prefix}{command.name} {command.signature}"
            embed.add_field(name=signature, value=command.help)

        return embed

    @commands.command()
    async def help(self, ctx: commands.Context, cog: t.Optional[str]) -> None:
        """Sends Bakerbot's documentation in a neatly formatted message."""
        view = DocumentationView(self.bot.cogs, self.embeddify)

        if cog is None:
            instructions = "Use the dropbown menu below to see help for a specific command group."
            await ctx.reply(instructions, view=view)
        else:
            cog = self.bot.cogs[cog.capitalize()]
            embed = self.embeddify(cog)
            await ctx.reply(embed=embed, view=view)

class DocumentationView(utilities.View):
    """A subclass of `utilities.View` for documenting commands."""
    def __init__(self, cogs: t.Mapping[str, commands.Cog], formatter: t.Callable, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.formatter = formatter
        self.cogs = cogs

        self.menu = discord.ui.Select(placeholder="Select any cog to view its commands.")
        self.menu.callback = self.cog_callback

        for name, cog in self.cogs.items():
            label = cog.__class__.__module__
            self.menu.add_option(label=label, value=name, description=cog.description)

        self.add_item(self.menu)

    async def cog_callback(self, interaction: discord.Interaction) -> None:
        """Handles cog selection requests from the Select Menu."""
        selection = self.menu.values[0]
        cog = self.cogs[selection]
        embed = self.formatter(cog)
        await interaction.response.edit_message(content=None, embed=embed)

def setup(bot: model.Bakerbot) -> None:
    cog = Helper(bot)
    bot.add_cog(cog)
