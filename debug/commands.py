import discord.app_commands as application
import discord.ext.commands as commands

import traceback
import discord
import logging
import colours
import typing
import limits

class Debug(commands.GroupCog):
    def __init__(self, bot: commands.Bot, logger: logging.Logger) -> None:
        super().__init__()
        self.logger = logger
        self.bot = bot

    @application.command(description="Synchronises application commands.")
    @application.describe(guild="The guild ID to sync to. If an ID is not specified, a global sync will be executed instead.")
    @application.describe(overwrite="Whether to copy global commands to the specified guild. This is ignored if a guild ID is not specified.")
    async def sync(self, interaction: discord.Interaction, guild: str | None, overwrite: bool=False) -> None:
        assert await self.bot.is_owner(interaction.user)

        if guild is None:
            await self.bot.tree.sync()
            await interaction.response.send_message("Global commands synchronised. Please wait up to **1 hour** for Discord to reflect any changes.", ephemeral=True)
            self.logger.info("Global commands synchronised.")

        elif overwrite:
            snowflake = discord.Object(guild)
            self.bot.tree.clear_commands(guild=snowflake)
            self.logger.info(f"Command tree cleared for guild ID {guild}.")

            self.bot.tree.copy_global_to(guild=snowflake)
            await self.bot.tree.sync(guild=snowflake)
            self.logger.info(f"Global commands copied and synchronised to guild ID {guild}.")

            for command in self.get_app_commands():
                self.logger.info(f"Re-adding command to guild tree: {command}")
                self.bot.tree.add_command(command, guild=snowflake)

            await interaction.response.send_message(f"Guild commands overwritten.")

        else:
            snowflake = discord.Object(guild)
            await self.bot.tree.sync(guild=snowflake)
            await interaction.response.send_message(f"Guild-specific commands synchronised.")
            self.logger.info(f"Guild-specific commands synchronised.")

    async def on_application_error(self, interaction: discord.Interaction, error: application.AppCommandError) -> None:
        trace = "".join(traceback.format_exception(error.__cause__ or error))
        command = interaction.command.name if interaction.command else "unknown"

        self.logger.error(f"Exception raised during execution of '{command}'.")
        self.logger.error(trace)

        embed = discord.Embed(
            title="Exception raised. See below for more information.",
            description=f"```{limits.limit(trace, limits.EMBED_DESCRIPTION - 6)}```",
            colour=colours.FAILURE
        )

        await interaction.response.send_message(embed=embed)
