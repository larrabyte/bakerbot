import model

import abc

class Model:
    """An abstract representation of a text generation model."""
    def __init__(self, backend: "Backend", identifier: str) -> None:
        self.backend = backend
        self.identifier = identifier
        self.remove_input = False
        self.temperature = 0.9
        self.maximum = 200
        self.repetition_penalty = 1.0

    async def generate(self, query: str) -> str:
        """Generate text using an initial query string."""
        return await self.backend.generate(self, query)

class Backend(abc.ABC):
    """An abstract representation of a text generation backend."""
    @abc.abstractclassmethod
    def name(cls) -> str:
        """Return the proper name of the API."""
        pass

    @abc.abstractclassmethod
    async def generate(cls, model: "Model", query: str) -> str:
        """Generate text using a model with an initial query string."""
        pass

def setup(bot: model.Bakerbot) -> None:
    pass
