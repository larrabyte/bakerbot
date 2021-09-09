import backend.utilities as utilities
import backend.wolfram as wolfram
import model

import discord.ext.commands as commands
import titlecase as tcase
import typing as t
import discord

class Wolfram(commands.Cog):
    """Bakerbot's interface to WolframAlpha. Supports unlimited requests and step-by-step solutions."""
    def __init__(self, bot: model.Bakerbot, backend: wolfram.Backend) -> None:
        self.backend = backend
        self.bot = bot

    @commands.command(aliases=["わ"])
    async def wa(self, ctx: commands.Context, *, query: str) -> None:
        """Queries WolframAlpha with `query`."""
        async with ctx.typing():
            params = self.backend.parameters(query, format="image", width="1500", mag="3")
            view = await WolframView.create(self.backend, params)

        if view is None:
            fail = utilities.Embeds.status(False, "WolframAlpha couldn't answer your query.")
            return await ctx.reply(embed=fail)

        data = "Press any button to view its content."
        await ctx.reply(data, view=view)

class WolframView(utilities.View):
    """A subclass of `utilities.View` for queries using the Full Results API."""
    @classmethod
    async def create(cls, backend: wolfram.Backend, params: dict) -> t.Optional["WolframView"]:
        instance = WolframView()
        instance.results = await backend.fullresults(params)
        if not backend.valid(instance.results):
            return None

        instance.backend = backend
        instance.params = params
        instance.cursor = 0

        instance.add_pod_buttons()
        return instance

    def images(self, pod: dict) -> str:
        """Returns available image links inside a pod."""
        links = (s["img"]["src"] for s in pod["subpods"])
        return "\n".join(links)

    def add_podstate_buttons(self, states: list) -> None:
        """Adds podstate buttons to the view's item list."""
        for state in states:
            if "states" in state:
                substates = state["states"]
                self.add_podstate_buttons(substates)
            else:
                name = state["name"][0:80]
                param = state["input"]
                identifier = utilities.Identifiers.generate(param)
                label = tcase.titlecase(name)

                button = discord.ui.Button(label=label, custom_id=identifier)
                button.callback = self.podstate_callback
                self.add_item(button)

    def add_pod_buttons(self) -> None:
        """Adds pod buttons to the view's item list."""
        pods = self.results["pods"]

        for index, pod in enumerate(pods):
            title = pod["title"][0:80]
            identifier = utilities.Identifiers.generate(index)
            title = tcase.titlecase(title)

            button = discord.ui.Button(label=title, custom_id=identifier)
            button.callback = self.pod_callback
            self.add_item(button)

    def add_control_buttons(self) -> None:
        """Adds control buttons to the view's item list."""
        identifier = utilities.Identifiers.generate("back")
        back = discord.ui.Button(label="Back", custom_id=identifier)
        back.callback = self.control_callback
        self.add_item(back)

    async def podstate_callback(self, interaction: discord.Interaction) -> None:
        """Handles podstate button presses."""
        # Defer the interaction as we need to make another request.
        embed = utilities.Embeds.standard()
        embed.description = "Please wait as another WolframAlpha API request is made."
        embed.set_footer(text="Interaction deferred.", icon_url=utilities.Icons.INFO)
        await interaction.response.edit_message(content=None, embed=embed, view=None)

        identifier = utilities.Identifiers.extract(interaction, str)
        self.params["podstate"] = identifier
        self.params["podindex"] = str(self.cursor + 1)

        results = await self.backend.fullresults(self.params)
        if not self.backend.valid(results):
            fail = utilities.Embeds.status(False, "WolframAlpha couldn't answer your query.")
            return await interaction.edit_original_message(content=None, embed=fail, view=None)

        self.clear_items()
        self.add_control_buttons()

        pod = results["pods"][0]
        if (states := pod.get("states", None)) is not None:
            self.add_podstate_buttons(states)

        data = self.images(pod)
        await interaction.edit_original_message(content=data, embed=None, view=self)

    async def pod_callback(self, interaction: discord.Interaction) -> None:
        """Handles pod-based button presses."""
        self.cursor = utilities.Identifiers.extract(interaction, int)
        self.clear_items()
        self.add_control_buttons()

        pod = self.results["pods"][self.cursor]
        if (states := pod.get("states", None)) is not None:
            self.add_podstate_buttons(states)

        data = self.images(pod)
        await interaction.response.edit_message(content=data, embed=None, view=self)

    async def control_callback(self, interaction: discord.Interaction) -> None:
        """Handles control button presses."""
        identifier = utilities.Identifiers.extract(interaction, str)
        data = "Press any button to view its content."

        if identifier == "back":
            self.clear_items()
            self.add_pod_buttons()
            await interaction.response.edit_message(content=data, embed=None, view=self)

def setup(bot: model.Bakerbot) -> None:
    backend = wolfram.Backend(bot.secrets, bot.session)
    cog = Wolfram(bot, backend)
    bot.add_cog(cog)
