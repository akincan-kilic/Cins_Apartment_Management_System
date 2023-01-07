import requests

class WeatherDataFetcher:
    def __init__(self) -> None:
        self.base_url = "https://api.open-meteo.com/v1/forecast?"
        self.default_coordinates = (38.6770, 27.3038) # Manisa Celal Bayar University

    def get_manisa_weather_data(self) -> dict:
        return self.fetch_weather_data(*self.default_coordinates)

    def fetch_weather_data(self, latitude, longitude, current_weather=True) -> dict:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": str(current_weather).lower(),
        }
        construct_url = self.base_url + "&".join([f"{key}={value}" for key, value in params.items()])
        response = requests.get(construct_url)
        return self.__parse_response(response.json())

    def __parse_response(self, response) -> dict:
        temperature = response["current_weather"]["temperature"]
        wind_speed = response["current_weather"]["windspeed"]
        wind_direction = response["current_weather"]["winddirection"]
        return {"temperature": temperature, "wind_speed": wind_speed, "wind_direction": wind_direction}

def main():
    fetcher = WeatherDataFetcher()
    data = fetcher.get_manisa_weather_data()
    print(data)

if __name__ == "__main__":
    main()
