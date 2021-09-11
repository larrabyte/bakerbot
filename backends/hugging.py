import exceptions
import model

import aiohttp
import ujson
import http

class UserModel:
    """A class representing each user's model configuration."""
    backend = "Hugging Face API"

    def __init__(self) -> None:
        self.identifier = "EleutherAI/gpt-neo-2.7B"
        self.remove_input = False
        self.temperature = 1.0
        self.maximum = 200

class Backend:
    """The Hugging Face API wrapper."""
    base = "https://api-inference.huggingface.co"
    session: aiohttp.ClientSession
    token: str

    @classmethod
    async def request(cls, endpoint: str, payload: dict, headers: dict) -> dict:
        """Sends a HTTP POST request to the Hugging Face Inference API."""
        async with cls.session.post(f"{cls.base}/{endpoint}", json=payload, headers=headers) as response:
            data = await response.read()

            if response.status != http.HTTPStatus.OK:
                try: formatted = ujson.loads(data)
                except ValueError: formatted = {}
                error = formatted.get("error", None)
                raise exceptions.HTTPUnexpected(response.status, error)

            return ujson.loads(data)

    @classmethod
    async def generate(cls, model: UserModel, query: str) -> str:
        """Generates text using `model`."""
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
        data = await cls.request(endpoint, payload, headers)
        return data[0]["generated_text"]

def setup(bot: model.Bakerbot) -> None:
    Backend.session = bot.session
    Backend.token = bot.secrets.get("hugging-token", None)
