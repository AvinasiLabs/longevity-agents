import pandas as pd
from pathlib import Path


ABS_PATH = Path(__file__).parent.parent


class Symbol2Pair:
    def __init__(self) -> None:
        self.coins = self.load_coins()

    def load_coins(self):
        """Load coins' slug and symbol, with the following fields:
            [id, symbol, slug]
        Returns:
            pd.DataFrame: the coins symbol and slug dataframe
        """
        fp = ABS_PATH.joinpath("assets/coins_symbol.csv")
        coins = pd.read_csv(str(fp))
        return coins

    def symbol2pair_binance_future(self, symbol):
        rec = self.coins.query(f'symbol == "{symbol.upper()}"')
        if not rec.empty:
            symbol = rec.iloc[0]["symbol"]
        else:
            rec = self.coins.query(f'slug.str.lower() == "{symbol.lower()}"')
            if not rec.empty:
                symbol = rec.iloc[0]["symbol"]
            else:
                return
        return f"{symbol}USDT"


if __name__ == "__main__":
    ...
