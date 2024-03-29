import discord.app_commands as application
import discord.ext.commands as commands

import traceback
import logging
import discord
import colours
import limits

async def dispatch(interaction: discord.Interaction, **kwargs):
    """Sends an embed to Discord, accounting for interaction responses."""
    if not interaction.response.is_done():
        await interaction.response.send_message(**kwargs)
    else:
        await interaction.edit_original_response(**kwargs)

async def on_command_error(context: commands.Context, error: commands.CommandError):
    """Handles text-based command errors."""
    logger = logging.getLogger(f"bakerbot.{__package__}")
    logger.error(f"Commmand error of type {type(error).__name__} raised, ignoring.")

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

async def on_view_error(interaction: discord.Interaction, error: Exception):
    """Handles view errors."""
    description = "".join(traceback.format_exception(error.__cause__ or error))

    logger = logging.getLogger(f"bakerbot.{__package__}")
    logger.error(f"Exception raised during execution of view.")
    logger.error(description)

    embed = discord.Embed(
        title="Exception raised. See below for more information.",
        description=f"```{limits.limit(description, limits.EMBED_DESCRIPTION - 6)}```",
        colour=colours.FAILURE
    )

    await dispatch(interaction, content=None, embed=embed)

async def on_check_failure(interaction: discord.Interaction, error: application.CheckFailure):
    """Handles application command permissions failure."""
    await dispatch(interaction, content="You are not allowed to execute this command.")
