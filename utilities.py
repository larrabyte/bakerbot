import discord

def file2ext(filepath: str):
    """Convert a filepath into a Python import path."""
    return filepath.replace("\\", ".").replace("/", ".").replace(".py", "")

def extstrip(cogname: str):
    """Strip any folders off a cog name."""
    return cogname.replace("cogs.", "")

def getembed(title: str, colour: int, footer: str=None):
    embed = discord.Embed(title=title, color=colour)
    embed.set_thumbnail(url="https://airbus-h.assetsadobe2.com/is/image/content/dam/channel-specific/website-/us/management/anthony-baker.jpg?wid=1000&qlt=85,0")
    if footer: embed.set_footer(text=footer)
    else: embed.set_footer(text="no footer :(")
    return embed
