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
    def generate(cls, obj: object) -> str:
        """Generates a random identifier (along with a bonus `str(obj)` if given)."""
        rand = os.urandom(cls.bytelength).hex()
        representation = str(obj)
        return f"{rand}{representation}"

    @classmethod
    def extract(cls, identifier: str) -> str:
        """Extracts the object representation passed in via `Identifiers.generate()`."""
        start = cls.bytelength * 2
        return identifier[start:]

class Embeds:
    @staticmethod
    def status(success: bool, description: str) -> discord.Embed:
        """Creates a standardised status embed."""
        status = "Operation successful!" if success else "Operation failed!"
        colour = Colours.success if success else Colours.failure
        icon = Icons.tick if success else Icons.cross

        embed = discord.Embed(colour=colour, timestamp=discord.utils.utcnow())
        embed.set_footer(text=status, icon_url=icon)
        embed.description = description
        return embed
