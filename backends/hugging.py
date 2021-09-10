import exceptions

import typing as t
import aiohttp
import ujson
import yarl

class Model:
    """A Hugging Face model."""
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self.temperature = 1.0
        self.maximum = 200
        self.noinput = False

class Backend:
    """The Hugging Face API wrapper."""
    def __init__(self, secrets: dict, session: aiohttp.ClientSession) -> None:
        self.base = "https://api-inference.huggingface.co"
        self.key = secrets.get("hugging-token", None)
        self.session = session

    async def request(self, path: str, payload: dict, headers: dict) -> t.Any:
        """Sends a HTTP POST request to the Hugging Face Inference API."""
        url = yarl.URL(f"{self.base}/{path}", encoded=True)

        async with self.session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json(encoding="utf-8", loads=ujson.loads)

            if resp.status != 200:
                if "error" in data:
                    message = data["error"]
                    raise exceptions.HTTPUnexpectedResponse(message)

                # If there isn't an error message, just raise a bad status exception.
                raise exceptions.HTTPBadStatus(200, resp.status)

            return data

    async def generate(self, model: Model, query: str) -> str:
        """Generates text using `model`."""
        if self.key is None:
            raise exceptions.SecretNotFound("hugging-token not found in secrets.json.")

        headers = {"Authorization": f"Bearer {self.key}"}

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

        path = f"models/{model.identifier}"
        data = await self.request(path, payload, headers)
        return data[0]["generated_text"]
