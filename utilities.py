import discord

ERRORCOLOUR = 0xFF5900
REGULARCOLOUR = 0x9A59B5
ECONOMYCOLOUR = 0xF5CC00

def getembed(title: str, footer: str=None, colour: int=REGULARCOLOUR, thumbnail: str=None):
    embed = discord.Embed(title=title, color=colour)
    if thumbnail: embed.set_thumbnail(url=thumbnail)
    else: embed.set_thumbnail(url="https://airbus-h.assetsadobe2.com/is/image/content/dam/channel-specific/website-/us/management/anthony-baker.jpg?wid=1000&qlt=85,0")
    if footer: embed.set_footer(text=footer)
    else: embed.set_footer(text="bitly.com/98K8eH")
    return embed
