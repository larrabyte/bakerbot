import utilities
import model

import discord.ext.commands as commands
import discord

class Meta(commands.Cog):
    """Stores information about Bakerbot."""
    def __init__(self, bot: model.Bakerbot) -> None:
        self.github = "https://github.com/larrabyte/bakerbot"
        self.bot = bot

    @commands.group(invoke_without_subcommand=True)
    async def meta(self, ctx: commands.Command) -> None:
        """The parent command for the meta cog."""
        summary = ("You've encountered Bakerbot's meta commands! "
                   "See `$help meta` for a full list of available subcommands.")

        await utilities.Commands.group(ctx, summary)

    @meta.command()
    async def invite(self, ctx: commands.Command) -> None:
        """Sends an invite for Bakerbot."""
        scopes = ("bot", "applications.commands")
        permissions = discord.Permissions(administrator=True)
        url = discord.utils.oauth_url(self.bot.application_id, permissions=permissions, scopes=scopes)

        view = discord.ui.View()
        button = discord.ui.Button(url=url, label="Click here to invite Bakerbot!")
        view.add_item(button)

        await ctx.reply("Check out the button below!", view=view)

    @meta.command()
    async def source(self, ctx: commands.Context) -> None:
        """Sends the GitHub link for Bakerbot."""
        view = discord.ui.View()
        button = discord.ui.Button(url=self.github, label="Click here to go to the repository!")
        view.add_item(button)

        await ctx.reply("Why not star the repo while you're there?", view=view)

    @meta.command()
    async def author(self, ctx: commands.Context) -> None:
        """Displays information about the author."""
        info = await self.bot.application_info()
        embed = utilities.Embeds.standard()
        embed.set_author(name=info.owner.display_name, url=self.github, icon_url=info.owner.display_avatar.url)
        embed.description = "Made by yours truly using `discord.py`."
        embed.set_footer(text="What do I even put here?", icon_url=utilities.Icons.INFO)
        await ctx.reply(embed=embed)

    @meta.command()
    async def guilds(self, ctx: commands.Context) -> None:
        """Displays information about Bakerbot's guilds."""
        member_count = sum(guild.member_count for guild in self.bot.guilds)
        guild_count = len(self.bot.guilds)
        average = round(member_count / guild_count)

        message = (f"Current Bakerbot statistics:\n"
                   f" • Total guild count: {guild_count}\n"
                   f" • Total member count: {member_count}\n"
                   f" • Average members per guild: {average}")

        await ctx.reply(message)

    @meta.command()
    async def ping(self, ctx: commands.Context) -> None:
        """Displays information about Bakerbot's connection to Discord."""
        latency = round(self.bot.latency * 1000, 2)
        await ctx.reply(f"Current websocket latency is {latency}ms.")

def setup(bot: model.Bakerbot) -> None:
    cog = Meta(bot)
    bot.add_cog(cog)
