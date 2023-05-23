from wolfram import backend, types

import discord.app_commands as application
import discord.ext.commands as commands

import discord
import logging
import aiohttp
import colours
import typing

class Wolfram(commands.Cog):
    def __init__(self, bot: commands.Bot, logger: logging.Logger, session: aiohttp.ClientSession):
        self.logger = logger
        self.bot = bot

        self.session = session

    @application.command(description="Ask Wolfram|Alpha something.")
    @application.describe(query="Enter what you want to calculate or know about.")
    async def wolfram(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(thinking=True)

        try:
            response = await backend.ask(self.session, query)
        except backend.Error as error:
            message = f"An unexpected error was returned: {error.reason}"
            return await interaction.followup.send(message)

        if response.capsules:
            view = View(self.session, response)
            await interaction.followup.send(view=view)
        else:
            content = "Wolfram|Alpha was unable to answer your query."
            await interaction.followup.send(content=content)

class View(discord.ui.View):
    """An interactive view for Wolfram|Alpha queries."""
    def __init__(self, session: aiohttp.ClientSession, response: types.Response):
        super().__init__()
        self.session = session
        self.parameters = response.parameters
        self.capsules = response.capsules

        self.add_capsule_buttons()

    def stringify(self, *objects: typing.Any) -> str:
        """Create an interaction ID suffixed with stringified Python objects."""
        # Hopefully no object has "|" in its string representation.
        return self.id + "|".join(str(element) for element in objects)

    def destringify(self, identifier: str) -> list[str]:
        """Convert an interaction ID into a list of stringified Python objects."""
        return identifier[len(self.id):].split("|")

    def add_capsule_buttons(self):
        """Add buttons for each capsule to the view."""
        for index, capsule in enumerate(self.capsules):
            button = discord.ui.Button(label=capsule.title, custom_id=self.stringify(index))
            button.callback = self.select
            self.add_item(button)

    def add_cherry_buttons(self, capsule: types.Capsule):
        """Add buttons for each cherry in a capsule to the view."""
        button = discord.ui.Button(label="Back", custom_id=self.stringify(capsule.id))
        button.callback = self.reset
        self.add_item(button)

        for cherry in capsule.cherries:
            button = discord.ui.Button(label=cherry.name, custom_id=self.stringify(cherry.input))
            button.callback = self.update
            self.add_item(button)

    async def reset(self, interaction: discord.Interaction):
        """Return the view to the capsule preview state."""
        self.clear_items()
        self.add_capsule_buttons()
        self.parameters.popall("includepodid", None)
        self.parameters.popall("podstate", None)
        await interaction.response.edit_message(embed=None, view=self)

    async def select(self, interaction: discord.Interaction):
        """Update the view to select a specific capsule."""
        identifier = interaction.data["custom_id"] # type: ignore

        index, = self.destringify(identifier)
        capsule = self.capsules[int(index)]

        self.clear_items()
        self.add_cherry_buttons(capsule)

        embed = discord.Embed(colour=colours.REGULAR)
        embeds = [embed.copy().set_image(url=url) for url in capsule.pictures]
        embeds[0].title = capsule.title

        await interaction.response.edit_message(embeds=embeds, view=self)

    async def update(self, interaction: discord.Interaction):
        """Update the view by requesting more information from Wolfram|Alpha."""
        # This is an extremely cursed system, but whatever.
        # The capsule identifier is encoded in the identifier of the Back button.
        # The cherry input is encoded in the identifier of the just-pressed button.
        # The type checker goes insane if I don't tell it to ignore what's happening here.
        back = self.children[0].custom_id # type: ignore
        identifier = interaction.data["custom_id"] # type: ignore

        pod, = self.destringify(back)
        state, = self.destringify(identifier)
        self.parameters["includepodid"] = pod
        self.parameters.add("podstate", state)

        self.clear_items()
        self.add_item(discord.ui.Button(label="Please wait while another request is made.", disabled=True))
        await interaction.response.edit_message(view=self)

        # We specified that only one capsule should be returned.
        response = await backend.request(self.session, self.parameters)
        capsule, = backend.parse(response)

        self.clear_items()
        self.add_cherry_buttons(capsule)

        embed = discord.Embed(colour=colours.REGULAR)
        embeds = [embed.copy().set_image(url=url) for url in capsule.pictures]
        embeds[0].title = capsule.title

        await interaction.edit_original_response(embeds=embeds, view=self)
