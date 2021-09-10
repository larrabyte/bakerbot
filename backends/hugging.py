import exceptions
import model

import typing as t
import aiohttp
import ujson
import http

class Model:
    """A Hugging Face model."""
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self.temperature = 1.0
        self.maximum = 200
        self.noinput = False

class Backend:
    """The Hugging Face API wrapper."""
    base = "https://api-inference.huggingface.co"
    session: aiohttp.ClientSession
    token: str

    @classmethod
    async def request(cls, endpoint: str, payload: dict, headers: dict) -> dict:
        """Sends a HTTP POST request to the Hugging Face Inference API."""
        async with cls.session.post(f"{cls.base}/{endpoint}", json=payload, headers=headers) as response:
            data = await response.json(encoding="utf-8", loads=ujson.loads)

            if response.status != http.HTTPStatus.OK:
                error = data.get("error", None)
                raise exceptions.HTTPUnexpected(response.status, error)

            return data

    @classmethod
    async def generate(cls, model: Model, query: str) -> str:
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
