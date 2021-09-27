import exceptions
import model

import ujson
import http

class Statistics:
    """A COVID-19 data object."""
    def __init__(self, data: dict) -> None:
        self.overseas: int = data["AcquiredOverseas"]
        self.local: int = data["AcquiredLocally"]
        self.deaths: int = data["Deaths"]
        self.new: int = data["NewCases"]
        self.tested: int = data["Tested"]
        self.cases: int = data["Cases"]
        self.interstate: int = data["AcquiredInterstate"]

class Backend:
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        cls.base = "https://nswdac-covid-19-postcode-heatmap.azurewebsites.net"
        cls.session = bot.session

    @classmethod
    async def get(cls, endpoint: str, **kwargs: dict) -> dict:
        """Sends a HTTP GET request to the COVID-19 API."""
        async with cls.session.get(f"{cls.base}/{endpoint}", **kwargs) as response:
            if response.status != http.HTTPStatus.OK:
                raise exceptions.HTTPUnexpected(response.status)

            return await response.json(encoding="utf-8", loads=ujson.loads)

    @classmethod
    async def statistics(cls) -> Statistics:
        """Returns COVID-19 statistics from the NSWDAC's API."""
        data = await cls.get("datafiles/statsLocations.json")
        data = data["data"][0]
        return Statistics(data)

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
