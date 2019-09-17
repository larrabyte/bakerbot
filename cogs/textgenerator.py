"""Adds some functions for retarded speech."""
from discord.ext import tasks, commands
from textgenrnn import textgenrnn

class textgenerator(commands.Cog):
    def __init__(self, bot):
        self.model = None
        self.bot = bot

    @commands.command()
    async def startengine(self, ctx):
        """Initialises the TensorFlow backend for text generation."""
        self.model = textgenrnn(weights_path="./data/teammagic_weights.hdf5", vocab_path="./data/teammagic_vocab.json", config_path="./data/teammagic_config.json")
        await ctx.send("TensorFlow initialised on GPU 0.")

    @commands.command()
    async def textgen(self, ctx, *, prefixtext: str=""):
        """Generates some text, optionally with a prefix and temperature."""
        if self.model == None: raise RuntimeError("Tensorflow uninitialised!")
        text = self.model.generate(n=5, prefix=prefixtext, temperature=1.0, return_as_list=True)
        for lines in text: await ctx.send(lines)

def setup(bot): bot.add_cog(textgenerator(bot))