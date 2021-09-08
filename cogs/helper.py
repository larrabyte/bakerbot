import backend.utilities as utilities
import model

import discord.ext.commands as commands
import discord

class Helper(commands.Cog):
    """Bakerbot's documentation lives here."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    @commands.command()
    async def help(self, ctx: commands.Context) -> None:
        """The help command for Bakerbot."""
        instructions = "Use the dropbown menu below to see help for a specific command group."
        view = HelperView(self.bot)
        await ctx.reply(instructions, view=view)

class HelperView(discord.ui.View):
    """A subclass of `discord.ui.View` for the help screen."""
    def __init__(self, bot: model.Bakerbot, *args: list, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.bot = bot

        self.menu = discord.ui.Select(placeholder="Select any cog to view its commands.")
        self.menu.callback = self.cog_callback

        for name, cog in self.bot.cogs.items():
            self.menu.add_option(label=cog.__class__.__module__, value=name, description=cog.description)

        self.add_item(self.menu)

    async def cog_callback(self, interaction: discord.Interaction) -> None:
        """Handles cog help requests."""
        selection = self.menu.values[0]
        cog = self.bot.cogs[selection]

        embed = utilities.Embeds.standard(description=cog.description)
        embed.title = f"Documentation for `{cog.__class__.__module__}`:"
        footer = "Arguments enclosed in <> are required while [] are optional."
        embed.set_footer(text=footer, icon_url=utilities.Icons.info)

        for command in cog.walk_commands():
            # We don't want group parent commands listed, ignore those.
            if isinstance(command, commands.Group):
                continue

            prefix = f"{command.full_parent_name} " if command.parent else ""
            signature = f"${prefix}{command.name} {command.signature}"
            embed.add_field(name=signature, value=command.help)

        await interaction.response.edit_message(content=None, embed=embed)

def setup(bot: model.Bakerbot) -> None:
    cog = Helper(bot)
    bot.add_cog(cog)
