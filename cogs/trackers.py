"""Background tasks."""
from discord.ext import tasks, commands
import discord
import asyncio
import random

class trackers(commands.Cog):
    def __init__(self, bot):
        self.songs = ["air_raid_siren.mp3", "yogscast-babayetu.mp3", "babayetu.mp3"]
        self.members = bot.get_all_members()
        self.civilisation = False
        self.bot = bot

        self.civtracker.start()

    @tasks.loop(seconds=5.0)
    async def civtracker(self):
        if self.civilisation: self.civtracker.cancel()
        players = [member for member in self.members if member.activity.name == "Sid Meier's Civilization VI"]
        
        if len(players) != 0:
            song = random.choice(self.songs)
            await self.bot.get_cog("voice").unifiedplay(players[0], "./ffmpeg/music/" + song)
            self.civilisation = True

    @civtracker.before_loop
    async def precivtracker(self):
        await self.bot.wait_until_ready()

def setup(bot): bot.add_cog(trackers(bot))