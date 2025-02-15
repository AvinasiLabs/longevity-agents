import asyncio
import aiofiles
import aiohttp
import json
import toml
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Literal, Callable
from pydantic import BaseModel
from urllib.parse import urljoin

# local module
from toolkit import GLOBAL_CONFIG
from utils.helpers import get_proxy
from utils.config_wrapper import BinanceDataCollectorConfig
from utils.logger import logger


ABS_PATH = Path(__file__).parent.parent.parent.parent
CONFIG_PATH = ABS_PATH.joinpath("toolkit/market_history/binance/config.toml")
CONFIG = toml.load(CONFIG_PATH)
CONFIG = BinanceDataCollectorConfig(proxy=GLOBAL_CONFIG["proxy"], **CONFIG)


SPECIAL_SYMBOLS = {
    "PEPEUSDT": "1000PEPEUSDT",
    "FLOKIUSDT": "1000FLOKIUSDT",
    "BONKUSDT": "1000BONKUSDT",
    "SATSUSDT": "1000SATSUSDT",
    "RATSUSDT": "1000RATSUSDT",
    "SHIBUSDT": "1000SHIBUSDT",
    "XECUSDT": "1000XECUSDT",
    "LUNCUSDT": "1000LUNCUSDT",
    "LUNAUSDT": "LUNC2USDT",
}


class BinanceOrder(BaseModel):
    sole_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    order_time: int
    interval: Literal[
        "1m",
        "3m",
        "5m",
        "15m",
        "30m",
        "1h",
        "2h",
        "4h",
        "6h",
        "8h",
        "12h",
        "1d",
        "3d",
        "1w",
        "1M",
    ] = "1m"
    before_second: float = CONFIG.data_setting.get("before_second", 1800)
    after_second: float = CONFIG.data_setting.get("after_second", 18000)
    api_type: str = "fapi"


class BinanceCollector:
    def __init__(self) -> None:
        self.config = CONFIG

    def construct_param(
        self,
        symbol,
        start_time: int,
        end_time: int,
        interval: str = "1m",
        limit: int = 1000,
    ):
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": int(start_time),
            "endTime": int(end_time),
            "limit": limit,
        }
        return params

    async def save_data_local(self, data, symbol, side, start_time: int, end_time: int):
        tz = timezone(timedelta(hours=8), "Beijing")
        t = datetime.now(tz=tz)
        st = datetime.fromtimestamp(start_time / 1000, tz=tz)
        st_str = st.strftime("%Y%m%d%H%M%S")
        et = datetime.fromtimestamp(end_time / 1000, tz=tz)
        et_str = et.strftime("%Y%m%d%H%M%S")

        fp = ABS_PATH.joinpath(
            f"data_collector/binance/data/{symbol}_{side}_{st_str}_{et_str}.json"
        )
        fp = str(fp)
        async with aiofiles.open(fp, "w") as f:
            text = json.dumps(data, indent=4)
            await f.write(text)
        logger.info(
            f'{t.strftime("%Y-%m-%d %H:%M:%S")} data saved: {fp}, from {st_str} to {et_str}'
        )

    async def get_kline(
        self,
        symbol,
        start_timestamp: int,
        end_timestamp: int,
        interval: str = "1m",
        sleep_s: float = 0.2,
        api_type: Literal["spot", "fapi", "dapi"] = "fapi",
    ):
        await asyncio.sleep(sleep_s)
        st = start_timestamp
        et = end_timestamp
        params = self.construct_param(symbol, st, et, interval=interval)
        # 构造期货K线api
        if api_type == "fapi":
            url = urljoin(self.config.api["fapi_base"], self.config.api["fapi_klines"])
        if api_type == "spot":
            url = urljoin(self.config.api["spot_base"], self.config.api["spot_klines"])
        proxy = self.config.proxy
        proxy = (
            get_proxy(
                is_static=proxy.is_static,
                host=proxy.host,
                port=proxy.port,
                api=proxy.api,
            )
            if proxy.is_used
            else None
        )
        try:
            async with aiohttp.ClientSession().get(
                url, params=params, proxy=proxy
            ) as resp:
                if resp.ok:
                    data = await resp.json()
                else:
                    raise ValueError(f"Bad request: {resp.status}")
        except Exception as e:
            raise e
        return data

    async def get_unit_return(
        self,
        symbol: str,
        st: int,
        et: int,
        sleep_s: float = 0.0001,
        api_type: Literal["spot", "fapi", "dapi"] = "fapi",
    ):
        data = await self.get_kline(symbol, st, et, sleep_s=sleep_s, api_type=api_type)
        open = data[0]
        close = data[-1]
        detla_ms = close[6] - open[0]
        op = float(open[1])
        cp = float(close[4])
        unit_return = math.log(cp / op) / detla_ms
        return unit_return * 1e10

    async def open_exam(
        self,
        symbol: str,
        side: Literal["BUY", "SELL"],
        st: int,
        et: int,
        threshold: float = 0.0,
        api_type: Literal["spot", "fapi", "dapi"] = "fapi",
    ):
        factor = 1 if side == "BUY" else -1
        if symbol in SPECIAL_SYMBOLS:
            symbol = SPECIAL_SYMBOLS[symbol]
        for _ in range(5):
            try:
                unit_r = await self.get_unit_return(
                    symbol, st, et, sleep_s=0.0001, api_type=api_type
                )
                if factor * unit_r >= factor * threshold:
                    return True
                else:
                    return False
            except:
                continue
        return False


if __name__ == "__main__":
    collector = BinanceCollector()
    order = BinanceOrder(
        sole_id="xxxxxx",
        symbol="SOLUSDT",
        side="BUY",
        order_time=datetime.strptime("20240807135000", "%Y%m%d%H%M%S").timestamp()
        * 1000,
        before_second=18000,
        after_second=1800,
    )
    symbol = order.symbol
    st = datetime.strptime("20240703213613", "%Y%m%d%H%M%S").timestamp() * 1000
    et = datetime.strptime("20240703225834", "%Y%m%d%H%M%S").timestamp() * 1000
    # data = asyncio.run(collector.get_kline(symbol, st, et))
    r = asyncio.run(collector.open_exam(symbol, "SELL", st, et))
    logger.info(r)
    ...
