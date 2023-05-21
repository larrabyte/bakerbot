import discord.app_commands as application

import traceback
import logging
import discord
import colours
import limits

async def dispatch(interaction: discord.Interaction, **parameters):
    """Sends an embed to Discord, accounting for interaction responses."""
    if not interaction.response.is_done():
        await interaction.response.send_message(**parameters)
    else:
        await interaction.followup.send(**parameters)

async def on_application_error(interaction: discord.Interaction, error: application.AppCommandError):
    """Handles application command errors."""
    if isinstance(error, application.CheckFailure):
        await on_check_failure(interaction, error)

    else:
        command = interaction.command.name if interaction.command is not None else "unknown"
        description = "".join(traceback.format_exception(error.__cause__ or error))

        logger = logging.getLogger(f"bakerbot.{__package__}")
        logger.error(f"Exception raised during execution of '{command}'.")
        logger.error(description)

        embed = discord.Embed(
            title="Exception raised. See below for more information.",
            description=f"```{limits.limit(description, limits.EMBED_DESCRIPTION - 6)}```",
            colour=colours.FAILURE
        )

        await dispatch(interaction, embed=embed)

async def on_check_failure(interaction: discord.Interaction, error: application.CheckFailure):
    """Handles application command permissions failure."""
    await dispatch(interaction, content="You are not allowed to execute this command.")
