"""Background tasks."""
from discord.ext import tasks, commands
import discord
import asyncio
import random

class trackers(commands.Cog):
    def __init__(self, bot):
        self.voice = bot.get_cog("voice")
        self.civilisation = False
        self.members = []
        self.bot = bot

        for guilds in bot.guilds: self.members += guilds.members
        self.civtracker.start()

    @tasks.loop(seconds=5.0)
    async def civtracker(self):
        if not self.civilisation:
            for member in self.members:
                if member.activity.name == "Sid Meier's Civilization VI":
                    song = random.choice(["./ffmpeg/music/air_raid_siren.mp3", "./ffmpeg/music/babayetu.mp3", "./ffmpeg/music/yogscast-babayetu.mp3"])
                    await self.voice.join(member)
                    await self.voice.play(member.guild.voice_client, song)
                    self.civilisation = True

def setup(bot): bot.add_cog(trackers(bot))