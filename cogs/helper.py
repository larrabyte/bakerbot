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
        embed = utilities.Embeds.standard()
        embed.description = "Use the dropbown menu below to see the help for a specific command group."
        embed.set_footer(text="Remember: the prefix is $ (and not +).", icon_url=utilities.Icons.info)
        view = HelperView(self.bot)
        await ctx.reply(embed=embed, view=view)

class HelperView(discord.ui.View):
    """A subclass of `discord.ui.View` for the help screen."""
    def __init__(self, bot: model.Bakerbot, *args: list, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.bot = bot

        self.menu = discord.ui.Select(placeholder="Select any cog to view its commands.")
        self.menu.callback = self.cog_callback

        for name, cog in self.bot.cogs.items():
            self.menu.add_option(label=name.lower(), value=name, description=cog.description)

        self.add_item(self.menu)

    async def cog_callback(self, interaction: discord.Interaction) -> None:
        """Handles cog help requests."""
        selection = self.menu.values[0]
        cog = self.bot.cogs[selection]

        embed = utilities.Embeds.standard()
        footer = "Arguments enclosed in <> are required while [] are optional."
        embed.set_footer(text=footer, icon_url=utilities.Icons.info)

        for command in cog.walk_commands():
            # We don't want group parent commands listed, ignore those.
            if isinstance(command, commands.Group):
                continue

            prefix = f"{command.full_parent_name} " if command.parent else ""
            embed.add_field(name=f"{prefix}{command.name} {command.signature}", value=command.help, inline=False)

        await interaction.response.edit_message(embed=embed)

def setup(bot: model.Bakerbot) -> None:
    cog = Helper(bot)
    bot.add_cog(cog)
