import exceptions

import typing as t
import aiohttp
import ujson
import yarl

class Model:
    """A Neuro model."""
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self.temperature = 1.0
        self.maximum = 200
        self.noinput = False

class Backend:
    """The Neuro API wrapper."""
    def __init__(self, secrets: dict, session: aiohttp.ClientSession) -> None:
        self.base = "https://api.neuro-ai.co.uk"
        self.key = secrets.get("neuro-token", None)
        self.session = session

    async def request(self, path: str, payload: dict, headers: dict) -> t.Any:
        """Sends a HTTP POST request to the Neuro API."""
        url = yarl.URL(f"{self.base}/{path}", encoded=True)

        async with self.session.post(url, json=payload, headers=headers) as resp:
            data = await resp.read()
            data = ujson.loads(data)

            if resp.status != 200:
                if "error" in data:
                    message = data["error"]
                    raise exceptions.HTTPUnexpectedResponse(message)

                raise exceptions.HTTPBadStatus(200, resp.status)

            return data

    async def generate(self, model: Model, query: str) -> str:
        """Generates text using `model`."""
        if self.key is None:
            raise exceptions.SecretNotFound("neuro-token not found in secrets.json.")

        headers = {"Authorization": f"Bearer {self.key}"}

        payload = {
            "modelId": model.identifier,
            "data": query,
            "input_kwargs": {
                "response_length": model.maximum,
                "remove_input": model.noinput,
                "temperature": model.temperature
            }
        }

        path = "SyncPredict?include_result=true"
        data = await self.request(path, payload, headers)

        if data["state"] == "ERROR":
            # API returned HTTP 200 status but still errored.
            message = data["result"]
            raise exceptions.HTTPUnexpectedResponse(message)

        return data["result"][0]["generated_text"]
