import exceptions
import model

import aiohttp
import ujson
import http

class Statistics:
    """A COVID-19 data object."""
    def __init__(self, data: dict) -> None:
        self.recovered = data.get("Recovered", None)
        self.overseas = data.get("AcquiredOverseas", None)
        self.local = data.get("AcquiredLocally", None)
        self.deaths = data.get("Deaths", None)
        self.new = data.get("NewCases", None)
        self.tested = data.get("Tested", None)
        self.cases = data.get("Cases", None)
        self.interstate = data.get("AcquiredInterstate", None)

class Backend:
    """The backend COVID-19 API wrapper."""
    base = "https://nswdac-covid-19-postcode-heatmap.azurewebsites.net"
    session: aiohttp.ClientSession

    @classmethod
    async def request(cls, endpoint: str) -> dict:
        """Sends a HTTP GET request to the COVID-19 API."""
        async with cls.session.get(f"{cls.base}/{endpoint}") as response:
            if response.status != http.HTTPStatus.OK:
                raise exceptions.HTTPUnexpected(response.status)

            return await response.json(encoding="utf-8", loads=ujson.loads)

    @classmethod
    async def statistics(cls) -> Statistics:
        """Returns COVID-19 statistics from the NSWDAC's API."""
        data = await cls.request("datafiles/statsLocations.json")
        data = data["data"][0]
        return Statistics(data)

def setup(bot: model.Bakerbot) -> None:
    Backend.session = bot.session
