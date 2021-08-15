import discord.ext.commands as commands
import asyncio
import discord
import model

class Magic(commands.Cog):
    """You can find dumb ideas from Team Magic here."""
    def __init__(self, bot: model.Bakerbot):
        self.colours = bot.utils.Colours
        self.icons = bot.utils.Icons
        self.embeds = bot.utils.Embeds
        self.magic = 473426067823263749
        self.sniper = False
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> None:
        # There are two conditions for running these commands:
        # the command is being run in Team Magic or I'm the one executing it.
        if ctx.guild.id == self.magic or (await self.bot.is_owner(ctx.author)):
            return True

        return False

    @commands.group(invoke_without_subcommand=True)
    async def magic(self, ctx: commands.Context) -> None:
        """The parent command for all things Team Magic related."""
        if ctx.invoked_subcommand is None:
            # Since there was no subcommand, inform the user about the group and its subcommands.
            desc = ("Welcome to the Team Magic command group. You can find dumb stuff here.\n"
                    "See `$help magic` for available subcommands.")

            embed = discord.Embed(description=desc, colour=self.colours.regular, timestamp=discord.utils.utcnow())
            embed.set_footer(text="These commands will only work inside Team Magic.", icon_url=self.icons.info)
            await ctx.reply(embed=embed)

    @magic.command()
    async def nodelete(self, ctx: commands.Context) -> None:
        """Enable/disable the message sniper."""
        self.sniper = not self.sniper
        description = f"on_message_delete() listener set to: `{self.sniper}`"
        embed = self.embeds.status(True, description)
        await ctx.reply(embed=embed)

    @magic.command()
    async def replace(self, ctx: commands.Context) -> None:
        """Enable/disable the word replacer."""
        self.replacement = not self.replacement
        description = f"on_message() listener set to: `{self.replacement}`"
        embed = self.embeds.status(True, description)
        await ctx.reply(embed=embed)

    @magic.command()
    async def demux(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str) -> None:
        """A demultiplexer experiment using Discord webhooks."""
        endpoints = await channel.webhooks()
        user, avatar = ctx.author.display_name, self.bot.user.avatar.url
        tasks = [hook.send(message, username=user, avatar_url=avatar) for hook in endpoints]
        await asyncio.gather(*tasks)

    @magic.command()
    async def hookify(self, ctx: commands.Context, target: discord.TextChannel) -> None:
        """So it turns out you can have more than 10 webooks in a channel..."""
        token = self.bot.secrets["discord-token"]
        headers = {"Authorization": f"Bot {token}"}
        payload = {"channel_id": target.id}
        endpoints = await ctx.channel.webhooks()
        moved = 0

        for hook in endpoints:
            url = f"https://discord.com/api/webhooks/{hook.id}"
            resp = await self.bot.session.patch(url, json=payload, headers=headers)
            moved += 1 if resp.status == 200 else 0

            if resp.status != 200:
                message = f"HTTP {resp.status} {resp.reason}\nWebhook {hook.id} was not moved.\n\n{resp.headers}"
                await ctx.reply(message)
                break

        await ctx.reply(f"{moved} webhooks were moved.")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Resends deleted messages. Triggered by the nodelete command."""
        if self.sniper and message.guild.id == self.magic:
            await message.channel.send(f"> Sent by {message.author.mention}\n{message.content}")

def setup(bot):
    cog = Magic(bot)
    bot.add_cog(cog)
