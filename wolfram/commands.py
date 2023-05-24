import discord.app_commands as application
import discord.ext.commands as commands
import wolfram.backend as backend

import discord
import aiohttp
import colours
import views

class Wolfram(commands.Cog):
    def __init__(self, bot: commands.Bot, session: aiohttp.ClientSession):
        self.session = session
        self.bot = bot

    @application.command(description="Ask Wolfram|Alpha something.")
    @application.describe(query="Enter what you want to calculate or know about.")
    async def wolfram(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(thinking=True)

        try:
            response = await backend.ask(self.session, query)
        except backend.Error as error:
            message = f"An unexpected error was returned: {error.reason}"
            return await interaction.followup.send(message)

        if response.pods:
            view = View(self.session, response)
            await interaction.followup.send(view=view)
        else:
            content = "Wolfram|Alpha was unable to answer your query."
            await interaction.followup.send(content=content)

class View(views.View):
    """An interactive view for Wolfram|Alpha queries."""
    def __init__(self, session: aiohttp.ClientSession, response: backend.Response):
        super().__init__()
        self.session = session
        self.parameters = response.parameters
        self.pods = response.pods

        self.add_pod_buttons()

    def add_pod_buttons(self):
        """Add buttons for each pod to the view."""
        for index, pod in enumerate(self.pods):
            button = discord.ui.Button(label=pod.title, custom_id=self.stringify(index))
            button.callback = self.select
            self.add_item(button)

    def add_state_buttons(self, pod: backend.Pod):
        """Add buttons for each state in a pod to the view."""
        button = discord.ui.Button(label="Back", custom_id=self.stringify(pod.id))
        button.callback = self.reset
        self.add_item(button)

        for state in pod.states:
            button = discord.ui.Button(label=state.name, custom_id=self.stringify(state.input))
            button.callback = self.update
            self.add_item(button)

    async def reset(self, interaction: discord.Interaction):
        """Return the view to the pod preview state."""
        self.clear_items()
        self.add_pod_buttons()
        self.parameters.popall("includepodid", None)
        self.parameters.popall("podstate", None)
        await interaction.response.edit_message(embed=None, view=self)

    async def select(self, interaction: discord.Interaction):
        """Update the view to select a specific pod."""
        identifier = interaction.data["custom_id"] # type: ignore

        index, = self.destringify(identifier)
        pod = self.pods[int(index)]

        self.clear_items()
        self.add_state_buttons(pod)

        embed = discord.Embed(colour=colours.REGULAR)
        embeds = [embed.copy().set_image(url=url) for url in pod.pictures]
        embeds[0].title = pod.title

        await interaction.response.edit_message(embeds=embeds, view=self)

    async def update(self, interaction: discord.Interaction):
        """Update the view by requesting more information from Wolfram|Alpha."""
        # This is an extremely cursed system, but whatever.
        # The pod identifier is encoded in the identifier of the Back button.
        # The state input is encoded in the identifier of the just-pressed button.
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
        pod, = backend.parse(response)

        self.clear_items()
        self.add_state_buttons(pod)

        embed = discord.Embed(colour=colours.REGULAR)
        embeds = [embed.copy().set_image(url=url) for url in pod.pictures]
        embeds[0].title = pod.title

        await interaction.edit_original_response(embeds=embeds, view=self)
