import asyncio
import aiohttp

class WeatherDataFetcher:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast?"
        self.manisa_celal_bayar_coordinates = (38.6770, 27.3038)
        # self.hourly = "temperature_2m"

    async def fetch_weather_data(self, latitude, longitude, current_weather=True, hourly=None):
        current_weather = str(current_weather).lower()
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": current_weather,
            "hourly": hourly
        }
        construct_url = self.base_url + "&".join([f"{key}={value}" for key, value in params.items()])
        print(construct_url)

        async with aiohttp.ClientSession() as session:
            async with session.get(construct_url) as response:
                return await response.json()

    def parse_response(self, response):
        temperature = response["current_weather"]["temperature"]
        wind_speed = response["current_weather"]["windspeed"]
        wind_direction = response["current_weather"]["winddirection"]
        return {"temperature": temperature, "wind_speed": wind_speed, "wind_direction": wind_direction}

    async def fetch_manisa_weather_data(self, current_weather=True):
        response = await self.fetch_weather_data(self.manisa_celal_bayar_coordinates[0],
                                             self.manisa_celal_bayar_coordinates[1],
                                             current_weather, self.hourly)
        return self.parse_response(response)

async def main():
    fetcher = WeatherDataFetcher()
    data = await fetcher.fetch_manisa_weather_data()
    print(data)

if __name__ == "__main__":
    asyncio.run(main())
