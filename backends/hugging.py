import exceptions
import model

import ujson
import http

class Model:
    """A class representing a Hugging Face model."""
    backend = "Hugging Face API"

    def __init__(self) -> None:
        self.identifier = "EleutherAI/gpt-neo-2.7B"
        self.remove_input = False
        self.temperature = 1.0
        self.maximum = 200

    async def generate(self, query: str) -> None:
        """Generates text using this model's configuration."""
        return await Backend.generate(self, query)

class Backend:
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        cls.base = "https://api-inference.huggingface.co"
        cls.session = bot.session
        cls.token = bot.secrets.get("hugging-token", None)

    @classmethod
    async def request(cls, endpoint: str, **kwargs: dict) -> dict:
        """Sends a HTTP POST request to the Hugging Face Inference API."""
        async with cls.session.post(f"{cls.base}/{endpoint}", **kwargs) as response:
            data = await response.read()

            if response.status != http.HTTPStatus.OK:
                try: formatted = ujson.loads(data)
                except ValueError: formatted = {}
                error = formatted.get("error", None)
                raise exceptions.HTTPUnexpected(response.status, error)

            return ujson.loads(data)

    @classmethod
    async def generate(cls, model: Model, query: str) -> str:
        """Generates text using the Hugging Face API."""
        if cls.token is None:
            raise exceptions.SecretNotFound("hugging-token not found in secrets.json.")

        headers = {"Authorization": f"Bearer {cls.token}"}

        payload = {
            "inputs": query,
            "options": {
                "use_cache": False,
                "wait_for_model": True
            },
            "parameters": {
                "max_length": model.maximum,
                "temperature": model.temperature
            }
        }

        endpoint = f"models/{model.identifier}"
        data = await cls.request(endpoint, json=payload, headers=headers)
        return data[0]["generated_text"]

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
