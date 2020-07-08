from discord.ext import tasks, commands
from random import randint
from utilities import *
import asyncio
import discord

class NotifierTask:
    def __init__(self, task: asyncio.Task, user: discord.Member, time: int):
        self.task = task
        self.user = user
        self.time = time

    def __repr__(self):
        return f"{self.user.mention}, {self.time}s"

class notifier(commands.Cog):
    """Implements the Bakerbot Notification System."""

    def __init__(self, bot):
        self.tasks = []
        self.bot = bot

    @tasks.loop(seconds=0.0)
    async def notifierloop(self, channel: discord.DMChannel, time: int, message: str):
        await channel.send(message)
        await asyncio.sleep(time)

    @commands.command()
    async def notiflist(self, ctx):
        """Show a list of all currently running notification tasks."""
        embed = getembed("Bakerbot Notification System", "servicing the notifications of dozens since 2020")
        iterator = 0

        for events in self.tasks:
            embed.add_field(name=f"Running Task #{iterator}", value=events, inline=False)
            iterator += 1

        await ctx.send(embed=embed)

    @commands.command()
    async def notify(self, ctx, time: str, user: discord.Member, *, message: str):
        """Shoot a DM someone's way when you want to remind them of something repeatedly.
           Default repetition rate is 1 minute. Specify time in s, m, h or d."""
        multiplier = time[-1]
        time = int(time[:-1])
        if multiplier == "s": pass
        elif multiplier == "m": time *= 60
        elif multiplier == "h": time *= 3600
        elif multiplier == "d": time *= 86400

        if not user.dm_channel: await user.create_dm()
        ntask = NotifierTask(self.notifierloop.start(user.dm_channel, time, message), user, time)
        await ctx.send(f"Notification task created for {user.mention}!")
        self.tasks.append(ntask)

    @commands.command()
    async def notifclear(self, ctx, index: int=None):
        """Immediately cancel a notification task, given an index to the task list."""
        if index == None:
            for events in self.tasks: events.task.cancel()
            self.tasks.clear()
            await ctx.send("BNS cleared!")
        else:
            ntask = self.tasks.pop(index)
            ntask.task.cancel()
            await ctx.send(f"BNS task #{index} cleared!")

def setup(bot): bot.add_cog(notifier(bot))
