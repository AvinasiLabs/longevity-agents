from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects


class VerifyCoin:
    def __init__(self, api_key) -> None:
        self.api_metadata = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/info"
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": api_key,
        }
        self.session = Session()
        self.session.headers.update(headers)

    def _get(self, url, params, proxies=None):
        try:
            response = self.session.get(url, params=params, proxies=proxies)
            data = response.json()
            return data
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            raise e
            # return

    def verify_coin(self, potential_coin: str, proxies=None):
        p_slug = {"slug": potential_coin.lower()}
        p_symbol = {"symbol": potential_coin}
        data = self._get(self.api_metadata, p_symbol, proxies=proxies)
        if data["status"]["error_code"] == 0:
            return f"{potential_coin} is cryptocurrency."
        data = self._get(self.api_metadata, p_slug, proxies=proxies)
        if data["status"]["error_code"] == 0:
            return f"{potential_coin} is cryptocurrency."
        return f"{potential_coin} is not cryptocurrency."


if __name__ == "__main__":
    ...
