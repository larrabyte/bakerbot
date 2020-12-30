from discord.ext import commands
import datetime as dt
import typing as t
import discord

class HelpError(commands.CommandError):
    COG_DOES_NOT_EXIST = (0, "That cog doesn't exist.")

    def __init__(self, error: tuple) -> None: self.error = error
    def __str__(self) -> str: return f"HelpError({self.error[0]}) raised: {self.error[1]}"

class Helper(commands.Cog, name="helper"):
    """Bakerbot's custom helper function lives here :)"""
    def __init__(self, bot: commands.Bot) -> None:
        bot.loop.create_task(self.startup())
        self.bot = bot

    async def startup(self) -> None:
        """Manages any cog prerequisites."""
        await self.bot.wait_until_ready()
        self.util = self.bot.get_cog("utilities")

    def help_embed(self, title: str, footer_text: str) -> discord.Embed:
        """Returns a Discord Embed for the help command."""
        embed = discord.Embed(title=title,
                              colour=self.util.regular_colour,
                              timestamp=dt.datetime.utcnow())

        embed.set_footer(text=footer_text, icon_url=self.util.note_icon)
        return embed

    @commands.command()
    async def help(self, ctx: commands.Context, cogname: t.Optional[str]) -> None:
        """Bakerbot's custom help function."""
        if cogname is None:
            cogs = [self.bot.cogs[name] for name in self.bot.cogs]
            embed = self.help_embed(title="Bakerbot: List of command groups.",
                                    footer_text="Note: typing $help [cogname] will display available commands in that cog.")

            for cog in cogs:
                embed.add_field(name=cog.qualified_name, value=cog.description, inline=False)
        else:
            cog = self.bot.get_cog(cogname)
            embed = self.help_embed(title=f"Bakerbot: List of commands in {cogname}.",
                                    footer_text="Note: arguments enclosed in <> are required while [] are optional.")
            
            if cog is None: raise HelpError(HelpError.COG_DOES_NOT_EXIST)
            for command in cog.walk_commands():
                if isinstance(command, commands.Group): continue
                prefix = f"{command.full_parent_name} " if command.parent else ""
                embed.add_field(name=f"{prefix}{command.name} {command.signature}", value=command.help, inline=False)

        await ctx.send(embed=embed)

def setup(bot): bot.add_cog(Helper(bot))
