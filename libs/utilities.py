import typing as t
import discord
import os

class Colours:
    regular = 0xF5CC00
    success = 0x00C92C
    failure = 0xFF3300
    gaming = 0x0095FF

class Icons:
    tick = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Flat_tick_icon.svg/500px-Flat_tick_icon.svg.png"
    cross = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Flat_cross_icon.svg/500px-Flat_cross_icon.svg.png"
    info = "https://icon-library.com/images/info-icon-svg/info-icon-svg-5.jpg"
    illuminati = "https://upload.wikimedia.org/wikipedia/commons/a/a9/Illuminati_triangle_eye.png"
    rfa = "https://upload.wikimedia.org/wikipedia/commons/4/40/Radio_Free_Asia_%28logo%29.png"
    wikipedia = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/500px-Wikipedia-logo-v2.svg.png"

class Identifiers:
    bytelength = 16

    @classmethod
    def generate(cls, obj: t.Any) -> str:
        """Generates a random identifier (along with a bonus `str(obj)` if given)."""
        rand = os.urandom(cls.bytelength).hex()
        representation = str(obj)
        return f"{rand}{representation}"

    @classmethod
    def extract(cls, interaction: discord.Interaction, obj: t.Any) -> t.Any:
        """Extracts the object representation passed in via `Identifiers.generate()`."""
        start = cls.bytelength * 2
        identifier = interaction.data["custom_id"]
        data = identifier[start:]
        return obj(data)

class Embeds:
    @staticmethod
    def standard(**kwargs: dict) -> discord.Embed:
        """Creates a standard Bakerbot embed."""
        embed = discord.Embed(colour=Colours.regular, timestamp=discord.utils.utcnow(), **kwargs)
        return embed

    @staticmethod
    def status(success: bool, description: str) -> discord.Embed:
        """Creates a standard Bakerbot status embed."""
        status = "Operation successful!" if success else "Operation failed!"
        colour = Colours.success if success else Colours.failure
        icon = Icons.tick if success else Icons.cross

        embed = discord.Embed(colour=colour, timestamp=discord.utils.utcnow())
        embed.set_footer(text=status, icon_url=icon)
        embed.description = description
        return embed

class Paginator(discord.ui.View):
    def __init__(self, placeholder: str="Options", *args: list, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.placeholder = placeholder
        self.menus = []
        self.page = 0

        # The value that was selected.
        self.selection = None

    def active(self) -> t.List[discord.ui.Select]:
        """Returns the list of active menus (according to `self.menus` and `self.page`)."""
        begin, end = 4 * self.page, 4 * (self.page + 1)
        return self.menus[begin:end]

    def generate(self) -> discord.ui.Select:
        """Returns a menu with an appropriate ID and placeholder."""
        n = len(self.menus)
        i = Identifiers.generate(n)

        text = f"{self.placeholder} {25 * n + 1} to {25 * n + 25}"
        menu = discord.ui.Select(custom_id=i, placeholder=text)
        menu.callback = self.callback
        return menu

    def add(self, option: discord.SelectOption) -> None:
        """Adds an item to the Paginator."""
        if not self.menus or len(self.menus[-1].options) == 25:
            menu = self.generate()
            self.menus.append(menu)

            if len(self.menus) < 5:
                self.add_item(menu)

        self.menus[-1].append_option(option)

    def display(self) -> None:
        """Displays the current page by adding appropriate UI elements."""
        for item in self.children.copy():
            if isinstance(item, discord.ui.Select):
                self.remove_item(item)

        for menu in self.active():
            self.add_item(menu)

    async def wait(self) -> t.Optional[str]:
        """Returns either the selected value or `None`."""
        await super().wait()
        return self.selection

    async def callback(self, interaction: discord.Interaction) -> None:
        """Called when a menu option is selected."""
        index = Identifiers.extract(interaction, int)
        self.selection = self.menus[index].values[0]
        self.stop()

    @discord.ui.button(label="First", row=4)
    async def first(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Moves the Paginator to the first page."""
        self.page = 0
        self.display()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Previous", row=4)
    async def prev(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Moves the Paginator to the previous page."""
        if self.page < 1:
            return await interaction.response.defer()

        self.page -= 1
        self.display()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Next", row=4)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Moves the Paginator to the next page."""
        if self.page >= -(-len(self.menus) // 4) - 1:
            return await interaction.response.defer()

        self.page += 1
        self.display()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Last", row=4)
    async def last(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Moves the Paginator to the last page."""
        self.page = -(-len(self.menus) // 4) - 1
        self.display()
        await interaction.response.edit_message(view=self)
