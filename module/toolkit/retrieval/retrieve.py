import numpy as np
from pathlib import Path
from typing import Literal
from aiohttp import ClientSession
from urllib.parse import urljoin

from utils.helpers import get_proxy, open_yaml_config
from utils.config_wrapper import RetrievalConfig
from utils.logger import logger


CONFIG_FP = Path(__file__).parent.joinpath("config.yaml")
CONFIG = open_yaml_config(str(CONFIG_FP))
CONFIG = RetrievalConfig(**CONFIG)


class Retriever:
    def __init__(self) -> None:
        self.base_url = f"http://{CONFIG.host}:{CONFIG.port}"
        self.api_map = CONFIG.api_map

    async def query_crypto_knowledge(self, queries: list):
        api = urljoin(self.base_url, self.api_map["crypto_knowledge"])
        form = dict(queries=queries)
        if CONFIG.proxy.is_used:
            proxy = get_proxy(
                is_static=CONFIG.proxy.is_static,
                host=CONFIG.proxy.host,
                port=CONFIG.proxy.port,
                api=CONFIG.proxy.api,
            )
        else:
            proxy = None
        try:
            async with ClientSession() as session:
                async with session.post(api, json=form, proxy=proxy) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result["result"]
                    else:
                        logger.info("Retrieval query_crypto_knowledge bad request.")
        except Exception as e:
            logger.info(e)
        return ""

    async def get_em(
        self, docs: list, method: Literal["dense", "sparse"] = "dense", is_pooled=True
    ):
        api = urljoin(self.base_url, self.api_map["embedding"])
        form = dict(docs=docs, mehtod=method)
        if CONFIG.proxy.is_used:
            proxy = get_proxy(
                is_static=CONFIG.proxy.is_static,
                host=CONFIG.proxy.host,
                port=CONFIG.proxy.port,
                api=CONFIG.proxy.api,
            )
        else:
            proxy = None
        try:
            async with ClientSession() as session:
                async with session.post(api, json=form, proxy=proxy) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        result = np.array(result)
                        if is_pooled:
                            result = np.mean(result, axis=0)
                        return result
                    else:
                        logger.info("Retrieval get_em bad request.")
        except Exception as e:
            logger.info(e)
        return ""

    async def find_simi(
        self, query: str, src_embeddings: np.ndarray, k=5, threshold=0.78
    ):
        tgt_emb = await self.get_em([query])
        cos = np.dot(src_embeddings, tgt_emb)
        scores, indices = self.topk(cos, k)
        index = []
        for i, score in enumerate(scores):
            if i == 5 or score < threshold:
                break
            index.append(indices[i])
        return index

    async def store_news(self, news_id, content, metadata):
        api = urljoin(self.base_url, self.api_map["store_news"])
        form = {"news_id": news_id, "content": content, "metadata": metadata}
        if CONFIG.proxy.is_used:
            proxy = get_proxy(
                is_static=CONFIG.proxy.is_static,
                host=CONFIG.proxy.host,
                port=CONFIG.proxy.port,
                api=CONFIG.proxy.api,
            )
        else:
            proxy = None
        try:
            async with ClientSession() as session:
                async with session.post(api, json=form, proxy=proxy) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result
                    else:
                        logger.info("Retrieval store_news bad request.")
        except Exception as e:
            logger.info(e)
        return ""

    @staticmethod
    def topk(vector: np.ndarray, k: int, axis=-1):
        """
        Returns the k largest elements along a given axis.

        Parameters:
        - vector: ndarray
            Input array
        - k: int
            Number of largest elements to return
        - axis: int (optional)
            Axis along which to find the k largest elements (default: -1)

        Returns:
        - values: ndarray
            k largest elements
        - indices: ndarray
            Indices of the k largest elements
        """
        if axis < 0:
            axis += vector.ndim
        indices = np.argsort(vector, axis=axis)[..., -k:]
        values = np.take_along_axis(vector, indices, axis=axis)
        return values, indices


if __name__ == "__main__":
    import asyncio

    retriever = Retriever()

    a = ["Former FTX Executive", "Ryan Salame"]
    # a = ['Ryan Salame', 'prison delay', 'dog attack', 'FTX Executive']
    b = ["CNBC", "Trump", "RFK Jr.", "Fort Knox", "bitcoin"]
    c = ["COINTELEGRAPH", "Judge", "ex-FTX exec"]
    # c = ["Judge", "grant", "postpone", "reporting to prison", "ex-FTX exec"]
    # a = asyncio.run(retriever.query_crypto_knowledge(query))
    # a = ['COINTELEGRAPH: Judge grants ex-FTX exec’s request to postpone reporting to prison']
    # b = ['Former FTX Executive Ryan Salame Granted Prison Delay After Dog Attack']
    c = [
        "CNBC: Trump didn't match RFK Jr.'s promise to build a 'bitcoin Fort Knox' — here's why"
    ]
    a = [
        """【Sydney SweeneyX账户遭到黑客攻击，宣传以其名字命名的加密货币】金色财经报道，美国女演员悉尼·斯威尼(Sydney Sweeney)的X账户遭到黑客攻击，其中发布的帖子宣传以她的名字命名的加密货币，目前这些帖子已被删除。 
基于Solana的代币SWEENEY于7月2日推出后的两个小时内就积累了超过1000万美元的交易量，这得益于Sweeney的X账户发布的多篇宣传帖子。从UTC时间下午6:15开始，SWEENEY的价格在短短一个多小时内下跌了近90%，不过此后有所反弹。DEX Screener数据显示，其市值目前为120万美元，低于385万美元的峰值。该token与一个Telegram频道的管理员（该频道在Sweeney的X账户上共享）似乎对这次黑客攻击负责。"""
    ]
    #     b = ['''【ZachXBT：Sydney Sweeney的X账户遭攻击与黑客Gurvinder Bhangu相关】金色财经报道，美国女演员Sydney Sweeney在 X 上遭受与加密货币相关的重大黑客攻击几周后，链上侦探 ZachXBT 在 X 上发布了他对最近 Sydney Sweeney 的 X 账户遭到黑客攻击事件的调查，以及被定罪的黑客 Gurvinder Bhangu 与该事件的涉嫌关联。
    # 7 月 2 日，这位女演员的 X 账户遭到黑客攻击，攻击者通过哄抬股价的手段推销基于 Solana 的代币 SWEENEY。根据 ZachXBT 的调查结果，Gurv 是此次黑客攻击的幕后黑手之一。Bhangu，在 ZachXBT 的帖子中也被称为“Gurv”，被描述为一名被定罪的黑客，曾因入侵 Instagram 账户并勒索用户而在英国短暂服刑。''']
    aem = asyncio.run(retriever.get_em(a, method="dense", is_pooled=False))
    bem = asyncio.run(retriever.get_em(b, method="dense", is_pooled=False))
    res = np.matmul(aem, bem.T)
    logger.info(res)
    logger.info(res.max())
    ...
