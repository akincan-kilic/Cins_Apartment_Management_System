import requests
from bs4 import BeautifulSoup


class CurrencyDataFetcher:
    EMPTY_CURRENCY_DATA = {'USD': 0, 'EUR': 0, 'GOLD_GR': 0, 'GBP': 0, 'BTC': 0}

    def __init__(self) -> None:
        self.url = "https://www.doviz.com/"
        self.gold_selector = self.get_nth_selector(1)
        self.usd_selector = self.get_nth_selector(2)
        self.eur_selector = self.get_nth_selector(3)
        self.sterling_selector = self.get_nth_selector(4)
        self.bitcoin_selector = self.get_nth_selector(6)

    @staticmethod
    def get_nth_selector(n: int) -> str:
        """
        On doviz.com the exchange rates are shown in the top of the page in the following order:
        1. (1GR) Gold, 2. USD, 3. EUR, 4. Sterling, 5. BIST, 6. Bitcoin, 7. Silver, 8. Brent
        """
        return f"body > header > div.header-secondary > div > div.market-data > div:nth-child({n}) > a > span.value"

    def fetch_exchange_rates(self) -> dict:
        html = requests.get(self.url).content
        soup = BeautifulSoup(html, "html.parser")

        usd = soup.select_one(self.usd_selector).text
        eur = soup.select_one(self.eur_selector).text
        gold = soup.select_one(self.gold_selector).text
        sterling = soup.select_one(self.sterling_selector).text
        bitcoin = soup.select_one(self.bitcoin_selector).text

        currency_dict = {'USD': usd, 'EUR': eur, 'GOLD_GR': gold, 'GBP': sterling, 'BTC': bitcoin}

        decimal_places = 4
        for key, value in currency_dict.items():
            convert_to_try = False
            if '$' in value:
                value = value.replace('$', '')
                convert_to_try = True

            currency_dict[key] = self.convert_string_number_to_float(value, decimal_places)

            if convert_to_try:
                converted_value = currency_dict['USD'] * currency_dict[key]
                currency_dict[key] = round(converted_value, 2)

        return currency_dict

    @staticmethod
    def convert_string_number_to_float(number: str, decimal_places: int) -> float:
        number = number.replace(".", "")
        number = number.replace(",", ".")
        number = float(number)
        return round(number, decimal_places)


def main():
    fetcher = CurrencyDataFetcher()
    data = fetcher.fetch_exchange_rates()
    print(data)


if __name__ == '__main__':
    main()
