import aiohttp
import ujson
import yarl

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
    """Backend COVID-19 API wrapper."""
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.base = "https://nswdac-covid-19-postcode-heatmap.azurewebsites.net"
        self.session = session

    async def request(self, path: str) -> dict:
        """Sends a HTTP GET request to the COVID-19 API."""
        url = yarl.URL(f"{self.base}/{path}")

        async with self.session.get(url) as resp:
            data = await resp.read()
            data = data.decode("utf-8")
            return ujson.loads(data)

    async def statistics(self) -> Statistics:
        """Returns COVID-19 statistics from the NSWDAC's API."""
        results = await self.request("datafiles/statsLocations.json")
        results = results["data"][0]
        stats = Statistics(results)
        return stats
