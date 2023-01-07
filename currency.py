import requests
from bs4 import BeautifulSoup

class CurrencyDataFetcher:
    def __init__(self) -> None:
        self.url = "https://www.doviz.com/"

    def fetch_exchange_rates(self) -> dict:
        html = requests.get(self.url).content
        soup = BeautifulSoup(html, "html.parser")
        usd = soup.select_one("#narrow-table-with-flag > tbody > tr:nth-child(1) > td:nth-child(2)").text
        eur = soup.select_one("#narrow-table-with-flag > tbody > tr:nth-child(2) > td:nth-child(2)").text
        return {'usd': usd, 'eur': eur}

def main():
    fetcher = CurrencyDataFetcher()
    data = fetcher.fetch_exchange_rates()
    print(data)
if __name__ == '__main__':
    main()