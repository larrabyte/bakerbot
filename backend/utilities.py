import discord.ext.commands as commands
import traceback as trace
import typing as t
import discord
import os

class Colours:
    REGULAR = 0xF5CC00
    SUCCESS = 0x00C92C
    FAILURE = 0xFF3300
    GAMING = 0x0095FF

class Icons:
    TICK = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Flat_tick_icon.svg/500px-Flat_tick_icon.svg.png"
    CROSS = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Flat_cross_icon.svg/500px-Flat_cross_icon.svg.png"
    INFO = "https://icon-library.com/images/info-icon-svg/info-icon-svg-5.jpg"

class Limits:
    MESSAGE_CHARACTERS = 2000
    MESSAGE_EMBEDS = 10
    EMBED_CHARACTERS = 6000
    EMBED_TITLE = 256
    EMBED_DESCRIPTION = 4096
    EMBED_FIELDS = 25
    EMBED_FIELD_NAME = 256
    EMBED_FIELD_VALUE = 1024
    EMBED_FOOTER_TEXT = 2048
    EMBED_AUTHOR_NAME = 256
    VIEW_CHILDREN = 25
    VIEW_ITEMS_PER_ROW = 5
    SELECT_LABEL = 100
    SELECT_VALUE = 100
    SELECT_DESCRIPTION = 100
    SELECT_OPTIONS = 25

    @staticmethod
    def limit(string: str, limit: int) -> str:
        """Limits a string to `limit` characters."""
        if len(string) > limit:
            return f"{string[0:limit - 3]}..."

        return string

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
        embed = discord.Embed(colour=Colours.REGULAR, timestamp=discord.utils.utcnow(), **kwargs)
        return embed

    @staticmethod
    def status(success: bool, description: str) -> discord.Embed:
        """Creates a standard Bakerbot status embed."""
        status = "Operation successful!" if success else "Operation failed!"
        colour = Colours.SUCCESS if success else Colours.FAILURE
        icon = Icons.TICK if success else Icons.CROSS

        embed = discord.Embed(colour=colour, timestamp=discord.utils.utcnow())
        embed.set_footer(text=status, icon_url=icon)
        embed.description = description
        return embed

class Commands:
    @staticmethod
    async def group(ctx: commands.Context, summary: str) -> None:
        """Handles standard parent group command behaviour."""
        if ctx.invoked_subcommand is None:
            if ctx.subcommand_passed is None:
                await ctx.reply(summary)
            else:
                classname = str(ctx.command.cog.__class__.__name__).lower()
                summary = f"`{ctx.subcommand_passed}` is not a valid subcommand of `${ctx.command.name}`."
                footer = f"Try $help {classname} for a list of subcommands."
                embed = Embeds.status(False, summary)
                embed.set_footer(text=footer, icon_url=Icons.CROSS)
                await ctx.reply(embed=embed)

class View(discord.ui.View):
    """A subclass of `discord.ui.View` that streamlines interaction error handling."""
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        embed = Embeds.status(False, "")
        embed.title = "Exception raised. See below for more information."

        # Extract traceback information if available.
        if (traceback := error.__traceback__) is not None:
            embed.title = "Exception raised. Traceback reads as follows:"

            for l in trace.extract_tb(traceback):
                embed.description += f"Error occured in {l[2]}, line {l[1]}:\n"
                embed.description += f"    {l[3]}\n"

        # Package the text/traceback data into an embed field and send it off.
        readable = str(error) or type(error).__name__
        embed.description += readable

        maximum = Limits.EMBED_CHARACTERS - (len(embed.title) + 6)
        embed.description = Limits.limit(embed.description, maximum)
        embed.description = f"```{embed.description}```"

        await interaction.edit_original_message(content=None, embed=embed, view=None)

class Paginator(View):
    """A subclass of `utilities.View` for paginating select menus."""
    def __init__(self, placeholder: str="Options", *args: list, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.placeholder = placeholder
        self.menus = []
        self.page = 0

        # The value that was selected.
        self.selection = None

    def active(self) -> t.List[discord.ui.Select]:
        """Returns the list of active menus (according to `self.menus` and `self.page`)."""
        constant = Limits.VIEW_ITEMS_PER_ROW - 1
        begin, end = constant * self.page, constant * (self.page + 1)
        return self.menus[begin:end]

    def generate(self) -> discord.ui.Select:
        """Returns a menu with an appropriate ID and placeholder."""
        n = len(self.menus)
        i = Identifiers.generate(n)
        lower = (Limits.SELECT_OPTIONS * n) + 1
        upper = Limits.SELECT_OPTIONS * (n + 1)

        text = f"{self.placeholder} {lower} to {upper}"
        menu = discord.ui.Select(custom_id=i, placeholder=text)
        menu.callback = self.callback
        return menu

    def add(self, option: discord.SelectOption) -> None:
        """Adds an item to the Paginator."""
        if not self.menus or len(self.menus[-1].options) == Limits.SELECT_OPTIONS:
            menu = self.generate()
            self.menus.append(menu)

            if len(self.menus) < Limits.VIEW_ITEMS_PER_ROW:
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
        constant = Limits.VIEW_ITEMS_PER_ROW - 1
        if self.page >= -(-len(self.menus) // constant) - 1:
            return await interaction.response.defer()

        self.page += 1
        self.display()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Last", row=4)
    async def last(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Moves the Paginator to the last page."""
        constant = Limits.VIEW_ITEMS_PER_ROW - 1
        self.page = -(-len(self.menus) // constant) - 1
        self.display()

        await interaction.response.edit_message(view=self)
