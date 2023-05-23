import discord
import debug

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
