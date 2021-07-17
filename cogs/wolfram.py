import discord.ext.commands as commands
import titlecase as tcase
import typing as t
import discord
import hashlib
import urllib
import model
import ujson
import yarl

class Wolfram(commands.Cog):
    """Houses an API wrapper for WolframAlpha (with unlimited requests)."""
    def __init__(self, bot: model.Bakerbot, backend: "WolframBackend") -> None:
        self.colours = bot.utils.Colours
        self.icons = bot.utils.Icons
        self.embeds = bot.utils.Embeds
        self.backend = backend
        self.bot = bot

    @commands.command()
    async def wa(self, ctx: commands.Context, *, query: str) -> None:
        """Ask WolframAlpha anything you want!"""
        async with ctx.typing():
            params = self.backend.parameters(query, format="image", width="1500", mag="3")
            view = await WolframView.create(cog=self, params=params)

        if view is None:
            fail = self.embeds.status(False, "WolframAlpha couldn't answer your query.")
            return await ctx.reply(embed=fail)

        data = "Press any button to view its content."
        await ctx.reply(data, view=view)

class WolframView(discord.ui.View):
    """A `discord.ui.View` subclass for WolframAlpha queries using the Full Results API."""
    @classmethod
    async def create(cls, cog: Wolfram, params: dict) -> t.Optional["WolframView"]:
        """Creates and returns an instance of `WolframView`."""
        instance = WolframView()
        instance.results = await cog.backend.fullresults(params)
        if not cog.backend.valid(instance.results):
            return None

        instance.ids = cog.bot.utils.Identifiers
        instance.colours = cog.bot.utils.Colours
        instance.embeds = cog.bot.utils.Embeds
        instance.icons = cog.bot.utils.Icons
        instance.params = params
        instance.cursor = 0
        instance.cog = cog

        instance.add_pod_buttons()
        return instance

    def images(self, pod: dict) -> str:
        """Returns available image links inside a pod."""
        links = [s["img"]["src"] for s in pod["subpods"]]
        return "\n".join(links)

    def add_podstate_buttons(self, states: list) -> None:
        """Adds podstate buttons to the view's item list."""
        for state in states:
            if "states" in state:
                substates = state["states"]
                self.add_podstate_buttons(substates)
            else:
                name = state["name"]
                param = state["input"]
                id = self.ids.generate(param)
                label = tcase.titlecase(name)

                button = discord.ui.Button(label=label, custom_id=id)
                button.callback = self.podstate_callback
                self.add_item(button)

    def add_pod_buttons(self) -> None:
        """Adds pod buttons to the view's item list."""
        pods = self.results["pods"]

        for index, pod in enumerate(pods):
            title = pod["title"]
            id = self.ids.generate(index)
            title = tcase.titlecase(title)

            button = discord.ui.Button(label=title, custom_id=id)
            button.callback = self.pod_callback
            self.add_item(button)

    def add_control_buttons(self) -> None:
        """Adds control buttons to the view's item list."""
        id = self.ids.generate("back")
        back = discord.ui.Button(label="Back", custom_id=id)
        back.callback = self.control_callback
        self.add_item(back)

    async def podstate_callback(self, interaction: discord.Interaction) -> None:
        """Handles podstate button presses."""
        # Defer the interaction as we need to make another request.
        embed = discord.Embed(colour=self.colours.regular, timestamp=self.embeds.now())
        embed.description = "Please wait as another WolframAlpha API request is made."
        embed.set_footer(text="Interaction deferred.", icon_url=self.icons.info)
        await interaction.response.edit_message(content=None, embed=embed, view=None)

        id = interaction.data["custom_id"]
        id = self.ids.extract(id)
        self.params["podstate"] = id
        self.params["podindex"] = str(self.cursor + 1)

        results = await self.cog.backend.fullresults(self.params)
        if not self.cog.backend.valid(results):
            fail = self.embeds.status(False, "WolframAlpha couldn't answer your query.")
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
        id = interaction.data["custom_id"]
        id = self.ids.extract(id)
        self.cursor = int(id)

        self.clear_items()
        self.add_control_buttons()

        pod = self.results["pods"][self.cursor]
        if (states := pod.get("states", None)) is not None:
            self.add_podstate_buttons(states)

        data = self.images(pod)
        await interaction.response.edit_message(content=data, embed=None, view=self)

    async def control_callback(self, interaction: discord.Interaction) -> None:
        """Handles control button presses."""
        id = interaction.data["custom_id"]
        id = self.ids.extract(id)
        data = "Press any button to view its content."

        if id == "back":
            self.clear_items()
            self.add_pod_buttons()
            await interaction.response.edit_message(content=data, embed=None, view=self)

class WolframBackend:
    """Backend WolframAlpha API wrapper."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.id = bot.secrets.get("wolfram-id", None)
        self.salt = bot.secrets.get("wolfram-salt", None)
        self.hashing = bot.secrets.get("wolfram-hash", False)
        self.session = bot.session

    @property
    def available(self) -> bool:
        """Checks whether the backend is available for use."""
        token = self.id is not None
        hashoff = self.hashing is False
        hashon = self.hashing is True and self.salt is not None
        return token and (hashon or hashoff)

    def valid(self, results: dict) -> bool:
        """Checks whether WolframAlpha gave a successful response."""
        success = results.get("success", False)
        error = results.get("error", True)
        return success and not error

    def digest(self, results: dict) -> str:
        """Returns an MD5 digest of `results`."""
        if self.salt is None:
            raise RuntimeError("Digest attempted without a salt.")

        values = [f"{k}{v}" for k, v in results.items()]
        data = f"{self.salt}{''.join(values)}"
        encoded = data.encode(encoding="utf-8")
        signature = hashlib.md5(encoded)
        return signature.hexdigest().upper()

    def parameters(self, query: str, **kwargs: dict) -> dict:
        """Generates a reasonable default dictionary of parameters (plus extras via kwargs)."""
        if self.id is None:
            raise RuntimeError("Parameter construction attempted without an ID.")

        params = {
            "appid": self.id,
            "format": "plaintext",
            "input": query,
            "output": "json",
            "reinterpret": "true"
        }

        params.update(kwargs)
        return params

    async def request(self, path: str) -> str:
        """Sends a HTTP GET request to the WolframAlpha API."""
        url = yarl.URL(path, encoded=True)
        print(url)

        async with self.session.get(url) as resp:
            data = await resp.read()
            data = data.decode("utf-8")
            return data

    async def fullresults(self, params: dict) -> dict:
        """Returns results from the Full Results API."""
        encoder = urllib.parse.quote_plus
        bypass = lambda string, safe, encoding, errors: string

        params = {k: encoder(v) for k, v in sorted(params.items())}
        encoded = urllib.parse.urlencode(params, quote_via=bypass)
        path = f"query.jsp?{encoded}"

        if self.hashing:
            digest = self.digest(params)
            path += f"&sig={digest}"

        v2base = "https://api.wolframalpha.com/v2"
        data = await self.request(f"{v2base}/{path}")

        try:
            data = ujson.loads(data)
            data = data["queryresult"]
        except (ValueError, KeyError):
            data = {}

        return data

def setup(bot: model.Bakerbot) -> None:
    backend = WolframBackend(bot)
    cog = Wolfram(bot, backend)
    bot.add_cog(cog)
