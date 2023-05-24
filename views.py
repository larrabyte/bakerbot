import discord
import typing
import limits
import debug

T = typing.TypeVar("T")

class View(discord.ui.View):
    """A discord.ui.View with a default error handler and custom ID methods."""
    def stringify(self, *objects) -> str:
        """Create an interaction ID suffixed with stringified Python objects."""
        # Hopefully no object has "|" in its string representation.
        return self.id + "|".join(str(element) for element in objects)

    def destringify(self, identifier: str) -> list[str]:
        """Convert an interaction ID into a list of stringified Python objects."""
        return identifier[len(self.id):].split("|")

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        """Called when an error occurs inside a view."""
        self.stop()
        await debug.errors.on_view_error(interaction, error)

class Paginator(View, typing.Generic[T]):
    """Let users select from a set of options."""
    def __init__(self, describer: typing.Callable[[T], tuple[str, str]], options: typing.Sequence[T]):
        super().__init__()
        self.describer = describer
        self.options = options
        self.selection = None

        # The current page can be extracted from
        # the values of the currently active options.
        self.set_menu_options(0)

    def get_menus(self) -> list[discord.ui.Select]:
        """Returns the list of menus."""
        return self.children[4:] # type: ignore

    def set_menu_options(self, page: int):
        """Set the menu options for the current page."""
        for _ in range(limits.VIEW_ITEMS_PER_ROW - 1 - len(self.get_menus())):
            menu = discord.ui.Select()
            menu.callback = self.select
            self.add_item(menu)

        for index, menu in enumerate(self.get_menus()):
            menu.options.clear()
            begin = limits.SELECT_OPTIONS * (page * (limits.VIEW_ITEMS_PER_ROW - 1) + index)    
            end = begin + limits.SELECT_OPTIONS

            for offset, option in enumerate(self.options[begin:end]):
                label, description = self.describer(option)
                menu.add_option(label=label, value=str(begin + offset), description=description)

            if not menu.options:
                self.remove_item(menu)

    async def wait(self) -> T | None:
        """Wait for an option to be chosen."""
        await super().wait()
        return self.selection

    async def select(self, interaction: discord.Interaction):
        """Select an option to return."""
        values = interaction.data["values"] # type: ignore
        value, = map(int, values)
        self.selection = self.options[value]
        self.stop()

    @discord.ui.button(label="First", row=4)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Move to the first page."""
        self.set_menu_options(0)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Previous", row=4)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Move to the previous page."""
        if not ((menus := self.get_menus()) and (options := menus[0].options)):
            return await interaction.response.defer()

        block = limits.SELECT_OPTIONS * (limits.VIEW_ITEMS_PER_ROW - 1)
        page = max(0, (int(options[0].value) // block) - 1)
        self.set_menu_options(page)

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Next", row=4)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Move to the next page."""
        if not ((menus := self.get_menus()) and (options := menus[0].options)):
            return await interaction.response.defer()

        block = limits.SELECT_OPTIONS * (limits.VIEW_ITEMS_PER_ROW - 1)
        page = min((len(self.options) // block) - 1, (int(options[0].value) // block) + 1)
        self.set_menu_options(page)

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Last", row=4)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Move to the last page."""
        block = limits.SELECT_OPTIONS * (limits.VIEW_ITEMS_PER_ROW - 1)
        page = max(0, (len(self.options) // block) - 1)
        self.set_menu_options(page)

        await interaction.response.edit_message(view=self)
