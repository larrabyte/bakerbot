from backends import wolfram
import utilities
import model

from discord.ext import commands
import typing as t
import titlecase
import discord

class Wolfram(commands.Cog):
    """Bakerbot's interface to WolframAlpha. Supports unlimited requests and step-by-step solutions."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.bot = bot

    @commands.command(aliases=["wa", "わ"])
    async def wolfram(self, ctx: commands.Context, *, query: str) -> None:
        """Query WolframAlpha with `query`."""
        async with ctx.typing():
            query = wolfram.Query(input=query, format="image", mag="3", width="1000", reinterpret="true")
            result = await wolfram.Backend.request(query)

        if not result.success:
            fail = utilities.Embeds.status(False)
            fail.description = "WolframAlpha was unable to answer your query."
            return await ctx.reply(embed=fail)

        view = WolframView(query, result)
        await ctx.reply("Press any button to view its content.", view=view)

class WolframView(utilities.View):
    """Displays results retrieved from WolframAlpha."""
    def __init__(self, query: wolfram.Query, result: wolfram.Result, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.query = query
        self.result = result
        self.current_pod = None

        self.show_pod_buttons()

    def format(self, pod: wolfram.Pod) -> t.List[discord.Embed]:
        blueprint = discord.Embed(colour=utilities.Colours.REGULAR)
        return [blueprint.copy().set_image(url=subpod.image.source) for subpod in pod.subpods]

    def show_pod_buttons(self) -> None:
        """Add buttons to the view that correspond to each pod in `self.result`."""
        for index, pod in enumerate(self.result.pods):
            label = utilities.Limits.limit(pod.title, utilities.Limits.SELECT_LABEL)
            label = titlecase.titlecase(label)
            identifier = utilities.Identifiers.generate(index)

            button = discord.ui.Button(label=label, custom_id=identifier)
            button.callback = self.pod_callback
            self.add_item(button)

    def show_podstate_buttons(self, pod: wolfram.Pod) -> None:
        """Add buttons to the view that correspond to each podstate in a pod."""
        for state in pod.states:
            label = utilities.Limits.limit(state["name"], utilities.Limits.SELECT_LABEL)
            label = titlecase.titlecase(label)
            identifier = utilities.Identifiers.generate(state["input"])

            button = discord.ui.Button(label=label, custom_id=identifier)
            button.callback = self.podstate_callback
            self.add_item(button)

    def show_control_buttons(self) -> None:
        """Add buttons to the view for control purposes."""
        identifier = utilities.Identifiers.generate("back")
        back = discord.ui.Button(label="Back", custom_id=identifier)
        back.callback = self.control_callback
        self.add_item(back)

    async def pod_callback(self, interaction: discord.Interaction) -> None:
        """Handle requests to view a pod."""
        cursor = utilities.Identifiers.extract(interaction, int)
        self.current_pod = self.result.pods[cursor]

        self.clear_items()
        self.show_control_buttons()
        self.show_podstate_buttons(self.current_pod)

        # Sending multiple embeds apparently means I need to defer.
        await interaction.response.defer()
        embeds = self.format(self.current_pod)
        await interaction.edit_original_message(content=None, embeds=embeds, view=self)

    async def podstate_callback(self, interaction: discord.Interaction) -> None:
        """Handle requests to update the current pod's podstate."""
        # Defer the interaction as we need to make another request.
        embed = utilities.Embeds.standard()
        embed.description = "Please wait while another WolframAlpha API request is made."
        embed.set_footer(text="Interaction deferred.", icon_url=utilities.Icons.INFO)
        await interaction.response.edit_message(content=None, embed=embed, view=None)

        identifier = utilities.Identifiers.extract(interaction, str)
        self.query.parameters["includepodid"] = self.current_pod.id
        self.query.parameters.add("podstate", identifier)

        result = await wolfram.Backend.request(self.query)
        pod = result.pods[0] if result.pods else self.current_pod

        if not result.success or not result.pods:
            fail = "WolframAlpha did not return any extra content."
            await interaction.followup.send(content=fail, ephemeral=True)

        self.clear_items()
        self.show_control_buttons()
        self.show_podstate_buttons(pod)

        embeds = self.format(pod)
        await interaction.edit_original_message(content=None, embeds=embeds, view=self)

    async def control_callback(self, interaction: discord.Interaction) -> None:
        """Handle control button requests."""
        identifier = utilities.Identifiers.extract(interaction, str)
        data = "Press any button to view its content."

        if identifier == "back":
            self.clear_items()
            self.show_pod_buttons()

            if "podstate" in self.query.parameters:
                del self.query.parameters["podstate"]

            await interaction.response.edit_message(content=data, embed=None, view=self)

def setup(bot: model.Bakerbot) -> None:
    cog = Wolfram(bot)
    bot.add_cog(cog)
