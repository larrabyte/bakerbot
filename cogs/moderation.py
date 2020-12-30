from discord.ext import commands
import datetime as dt
import typing as t
import discord

class Moderation(commands.Cog, name="moderation"):
    """A class of moderation commands."""
    def __init__(self, bot: commands.Bot) -> None:
        bot.loop.create_task(self.startup())
        self.bot = bot

    async def startup(self) -> None:
        """Manages any cog prerequisites."""
        await self.bot.wait_until_ready()
        self.util = self.bot.get_cog("utilities")

    @commands.command()
    async def purge(self, ctx: commands.Context, channel: t.Optional[discord.TextChannel], n: int) -> None:
        """Purge n messages in the current channel (or an optional channel of your choosing)."""
        channel = ctx.channel if channel is None else channel
        async for message in channel.history(limit=n):
            await message.delete()

        await ctx.send(embed=self.util.status_embed(
            ctx=ctx, success=True, title="Bakerbot: Message purger.",
            description=f"{n} messages successfully purged!"
        ))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Fired after a member joins a Guild."""
        with self.bot.get_guild(self.util.aa_server_id) as aa:
            if member.guild == aa: await member.add_roles(aa.get_role(self.util.aa_defrole_id))

def setup(bot): bot.add_cog(Moderation(bot))
