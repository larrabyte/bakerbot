from libs.utilities import Embeds, Colours, Icons
from libs.models import Bakerbot
from discord.ext import commands

import discord
import random

class Magic(commands.Cog):
    """You can find dumb ideas from Team Magic here."""
    def __init__(self, bot: Bakerbot):
        self.magic_guild_id = 473426067823263749
        self.omd_enable = False
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> None:
        # Ensure that these commands can only be run from Team Magic.
        if ctx.guild.id == self.magic_guild_id:
            return True

        return False

    @commands.group(invoke_without_subcommand=True)
    async def magic(self, ctx: commands.Context) -> None:
        """The parent command for all things Team Magic related."""
        if ctx.invoked_subcommand is None:
            # Since there was no subcommand, inform the user about the module manager and its subcommands.
            desc = ("Welcome to the Team Magic command group. You can find dumb stuff here.\n"
                    "See `$help magic` for available subcommands.")

            embed = discord.Embed(description=desc, colour=Colours.regular, timestamp=Embeds.now())
            embed.set_footer(text="These commands will only work inside Team Magic.", icon_url=Icons.info)
            await ctx.send(embed=embed)

    @magic.command()
    async def nodelete(self, ctx: commands.Context) -> None:
        """Enable/disable the message sniper."""
        self.omd_enable = not self.omd_enable
        embed = Embeds.status(success=True, desc=f"on_message_delete() listener set to: `{self.omd_enable}`")
        await ctx.send(embed=embed)

    @magic.command()
    async def tribute(self, ctx: commands.Context) -> None:
        """Plays a random tribute from the dinosaur tribute playlist. Thanks Ethan."""
        playlist = "https://www.youtube.com/playlist?list=PLwHlud7W_cz-yWZOvfQVeg21H018zPIk3"
        voice = self.bot.get_cog("Voice")

        tracks = await voice.get_tracks(query=playlist, search=False, single=False)
        track = random.choice(tracks)
        m, s = voice.get_formatted_length(track.length, fixed=True)

        embed = discord.Embed(colour=Colours.regular, timestamp=Embeds.now())
        embed.description = f"[{track.title}]({track.uri}) `[{m}:{s}]`"
        embed.set_footer(text="Enjoy your fetish.", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        # Resends deleted messages. Triggered by the nodelete command.
        if not self.omd_enable: return

        if message.guild.id == self.magic_guild_id:
            await message.channel.send(f"> Sent by {message.author.mention}\n{message.content}")

def setup(bot): bot.add_cog(Magic(bot))
