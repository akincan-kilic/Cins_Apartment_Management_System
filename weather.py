import requests
from bs4 import BeautifulSoup


class WeatherDataFetcherAPI:
    def __init__(self) -> None:
        self.base_url = "https://api.open-meteo.com/v1/forecast?"
        self.default_coordinates = (38.6770, 27.3038)  # Manisa Celal Bayar University

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
        return self.__parse_weather_api_response(response.json())

    @staticmethod
    def __parse_weather_api_response(response) -> dict:
        temperature = response["current_weather"]["temperature"]
        wind_speed = response["current_weather"]["windspeed"]
        wind_direction = response["current_weather"]["winddirection"]
        return {"temperature": temperature, "wind_speed": wind_speed, "wind_direction": wind_direction}


class WeatherDataFetcher:
    EMPTY_WEATHER_DATA = {'weather_description': '',
                          'temperature_celcius': 0,
                          'day_temp_celcius': 0,
                          'night_temp_celcius': 0}

    def __init__(self):
        self.url = "https://weather.com/weather/today/l/ca1734833d25fb15fd8de8c52fae8352c220c7200a6414348b48b4be5bebbead"
        self.degree_character = "°"
        self.temperature_selector = "#WxuCurrentConditions-main-eb4b02cb-917b-45ec-97ec-d4eb947f6b6a > div > section > div > div.CurrentConditions--body--l_4-Z > div.CurrentConditions--columns--30npQ > div.CurrentConditions--primary--2DOqs > span"
        self.weather_description_selector = "#WxuCurrentConditions-main-eb4b02cb-917b-45ec-97ec-d4eb947f6b6a > div > section > div > div.CurrentConditions--body--l_4-Z > div.CurrentConditions--columns--30npQ > div.CurrentConditions--primary--2DOqs > div.CurrentConditions--phraseValue--mZC_p"
        self.day_temp_selector = "#WxuCurrentConditions-main-eb4b02cb-917b-45ec-97ec-d4eb947f6b6a > div > section > div > div.CurrentConditions--body--l_4-Z > div.CurrentConditions--columns--30npQ > div.CurrentConditions--primary--2DOqs > div.CurrentConditions--tempHiLoValue--3T1DG > span:nth-child(1)"
        self.night_temp_selector = "#WxuCurrentConditions-main-eb4b02cb-917b-45ec-97ec-d4eb947f6b6a > div > section > div > div.CurrentConditions--body--l_4-Z > div.CurrentConditions--columns--30npQ > div.CurrentConditions--primary--2DOqs > div.CurrentConditions--tempHiLoValue--3T1DG > span:nth-child(2)"
        self.wind_selector = "#todayDetails > section > div.TodayDetailsCard--detailsContainer--2yLtL > div:nth-child(2) > div.WeatherDetailsListItem--wxData--kK35q > span"

    def parse_weather(self):
        html = requests.get(self.url).content
        soup = BeautifulSoup(html, "html.parser")

        weather_description = soup.select_one(self.weather_description_selector).text

        temperature_text = soup.select_one(self.temperature_selector).text
        day_temp_text = soup.select_one(self.day_temp_selector).text
        night_temp_text = soup.select_one(self.night_temp_selector).text

        temperature_fahrenheit = self.__convert_temperature_to_int(temperature_text)
        day_temp_fahrenheit = self.__convert_temperature_to_int(day_temp_text)
        night_temp_fahrenheit = self.__convert_temperature_to_int(night_temp_text)

        temperature_celcius = self.fahrenheit_to_celcius(temperature_fahrenheit)
        day_temp_celcius = self.fahrenheit_to_celcius(day_temp_fahrenheit)
        night_temp_celcius = self.fahrenheit_to_celcius(night_temp_fahrenheit)

        return {'weather_description': weather_description,
                'temperature_celcius': temperature_celcius,
                'day_temp_celcius': day_temp_celcius,
                'night_temp_celcius': night_temp_celcius}

    def fetch_weather_data(self, city):
        if city == "Manisa":
            return self.parse_weather()
        return self.EMPTY_WEATHER_DATA

    def __convert_temperature_to_int(self, temperature):
        temperature = temperature.replace(self.degree_character, "")
        temperature = int(temperature)
        return temperature

    @staticmethod
    def fahrenheit_to_celcius(fahrenheit):
        return round((fahrenheit - 32) * 5 / 9, 1)


def main():
    # fetcher = WeatherDataFetcher()
    # data = fetcher.get_manisa_weather_data()
    # print(data)
    fetcher = WeatherDataFetcher()
    data = fetcher.parse_weather()
    print(data)


if __name__ == "__main__":
    main()
