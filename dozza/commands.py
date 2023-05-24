import discord.app_commands as application
import discord.ext.commands as commands
import dozza.backend as backend

import discord
import aiohttp
import asyncio

class Dozza(commands.Cog):
    def __init__(self, bot: commands.Bot, session: aiohttp.ClientSession):
        self.session = session
        self.bot = bot

    @application.command(description="Get a fucking joke.")
    async def joke(self, interaction: discord.Interaction):
        # Jokes could take a while to come back.
        await interaction.response.defer(thinking=True)

        try:
            joke = await backend.funny(self.session)
        except backend.Error as error:
            message = f"An unexpected error occurred during joke fetching: {error.reason}"
            return await interaction.followup.send(message)

        await interaction.followup.send(joke.quip)

        if joke.followup is not None:
            await asyncio.sleep(3.0)
            await interaction.edit_original_response(content=f"{joke.quip}\n{joke.followup}")
