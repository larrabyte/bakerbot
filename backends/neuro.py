import exceptions
import model

import aiohttp
import ujson
import http

class Model:
    """A Neuro model."""
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self.temperature = 1.0
        self.maximum = 200
        self.noinput = False

class Backend:
    """The Neuro API wrapper."""
    base = "https://api.neuro-ai.co.uk"
    session: aiohttp.ClientSession
    token: str

    @classmethod
    async def request(cls, endpoint: str, parameters: dict, payload: dict, headers: dict) -> dict:
        """Sends a HTTP POST request to the Neuro API."""
        async with cls.session.post(f"{cls.base}/{endpoint}", params=parameters, json=payload, headers=headers) as response:
            data = await response.json(encoding="utf-8", loads=ujson.loads)

            if response.status != http.HTTPStatus.OK:
                error = data.get("error", None)
                raise exceptions.HTTPUnexpected(response.status, error)

            return data

    @classmethod
    async def generate(cls, model: Model, query: str) -> str:
        """Generates text using `model`."""
        if cls.token is None:
            raise exceptions.SecretNotFound("neuro-token not found in secrets.json.")

        parameters = {"include_result": "true"}
        headers = {"Authorization": f"Bearer {cls.token}"}

        payload = {
            "modelId": model.identifier,
            "data": query,
            "input_kwargs": {
                "response_length": model.maximum,
                "remove_input": model.noinput,
                "temperature": model.temperature
            }
        }

        data = await cls.request("SyncPredict", parameters, payload, headers)

        if data["state"] == "ERROR":
            # API returned HTTP 200 OK, but there's still an error.
            status = http.HTTPStatus.OK
            message = data["result"]
            raise exceptions.HTTPUnexpected(status, message)

        return data["result"][0]["generated_text"]

def setup(bot: model.Bakerbot) -> None:
    Backend.session = bot.session
    Backend.token = bot.secrets.get("neuro-token", None)
