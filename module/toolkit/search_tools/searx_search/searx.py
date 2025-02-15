#! python3
# -*- encoding: utf-8 -*-
"""
@Time: 2024/05/10 11:24:27
@Author: Louis
@Version: 1.0
@Contact: lululouisjin@gmail.com
@Description: The Searx search engine, a powerful and free search engine with multiple search sources like google, bing, yanex, etc.
"""


from pathlib import Path

ABS_PATH = Path(__file__).parent.parent.parent

import random
import requests
import httpx
import yaml
from typing import List, Literal
from lxml import etree
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import urljoin

# local module
from utils.helpers import get_proxies, get_proxy, open_yaml_config
from utils.logger import logger


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}
CONFIG_PATH = str(ABS_PATH.joinpath("toolkit/searx_search/config.yaml"))
GLOBAL_CONFIG_PATH = str(ABS_PATH.joinpath("assets/global_config.yaml"))
GLOBAL_CONFIG = open_yaml_config(GLOBAL_CONFIG_PATH)


class ProxyConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    is_used: bool = False
    is_static: bool = True
    host: str = "127.0.0.1"
    port: int = 26003
    api: str = ""


class SearxSearchConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    proxy: ProxyConfig = ProxyConfig()
    src_urls: List[str] = None


class SearxSearch:
    def __init__(self, use_local_urls=True) -> None:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        config.update({"proxy": GLOBAL_CONFIG["proxy"]})
        self.config = SearxSearchConfig(**config)
        self.src_urls = self.init_src(use_local_urls)

    def init_src(self, use_local_urls=False):
        """Get the search engine url list from Searx space. If failed, use the local url list.

        Returns:
            list: The url list for searx search engines.
        """
        if use_local_urls:
            return self.config.src_urls
        proxy = self.config.proxy
        space_url = "https://searx.space/data/instances.json"
        try:
            resp = (
                requests.get(
                    space_url,
                    proxies=get_proxies(
                        proxy.is_static, proxy.host, proxy.port, proxy.api
                    ),
                )
                if proxy.is_used
                else requests.get(space_url)
            )
            urls = resp.json()
            urls = list(urls["instances"].keys())
        except:
            urls = self.config.src_urls
        return urls

    def search(
        self,
        query: str,
        src_url: str = None,
        category: Literal["category_general", "category_news"] = "category_general",
        language: Literal["auto", "all", "en", "zh"] = "auto",
        time_range: Literal["", "day", "week", "month", "year"] = "",
        safesearch=0,
        theme="simple",
        k=10,
    ):
        for retry in range(5):
            r_text = self.request(
                query, src_url, category, language, time_range, safesearch, theme
            )
            answer = self.parse(r_text, k)
            if answer:
                return answer
        return answer

    async def a_search(
        self,
        query: str,
        src_url: str = None,
        category: Literal["category_general", "category_news"] = "category_general",
        language: Literal["auto", "all", "en", "zh"] = "auto",
        time_range: Literal["", "day", "week", "month", "year"] = "",
        safesearch=0,
        theme="simple",
        k=10,
    ):
        for retry in range(5):
            r_text = await self.a_request(
                query, src_url, category, language, time_range, safesearch, theme
            )
            answer = self.parse(r_text, k)
            if answer:
                return answer
        return answer

    def request(
        self,
        query: str,
        src_url: str = None,
        category: Literal["category_general", "category_news"] = "category_general",
        language: Literal["auto", "all", "en", "zh"] = "auto",
        time_range: Literal["", "day", "week", "month", "year"] = "",
        safesearch=0,
        theme="simple",
    ):
        if not src_url:
            src_url = random.choice(self.src_urls)
        params = {
            "q": query,
            category: "",
            "language": language,
            "time_range": time_range,
            "safesearch": safesearch,
            "theme": theme,
        }
        proxy = self.config.proxy
        # retry for 5 times if request fails
        max_try = 0
        while True:
            try:
                resp = requests.get(
                    src_url,
                    params=params,
                    headers=HEADERS,
                    proxies=(
                        get_proxies(proxy.is_static, proxy.host, proxy.port, proxy.api)
                        if proxy.is_used
                        else None
                    ),
                )
                if resp.ok:
                    return resp.text
            except Exception as e:
                logger.info(e)
            max_try += 1
            if max_try > 5:
                return ""
            src_url = random.choice(self.src_urls)

    async def a_request(
        self,
        query: str,
        src_url: str = None,
        category: Literal["category_general", "category_news"] = "category_general",
        language: Literal["auto", "all", "en", "zh"] = "auto",
        time_range: Literal["", "day", "week", "month", "year"] = "",
        safesearch=0,
        theme="simple",
        timeout=30,
    ):
        if not src_url:
            src_url = random.choice(self.src_urls)
            src_url = urljoin(src_url, "search")
        params = {
            "q": query,
            category: "",
            "language": language,
            "time_range": time_range,
            "safesearch": safesearch,
            "theme": theme,
        }
        proxy = self.config.proxy
        proxy = (
            get_proxy(proxy.is_static, proxy.host, proxy.port, proxy.api)
            if proxy.is_used
            else None
        )
        # retry for 5 times if request fails
        max_try = 0
        async with httpx.AsyncClient(headers=HEADERS, proxies=proxy) as session:
            while True:
                try:
                    resp = await session.get(src_url, params=params, timeout=timeout)
                    if resp.status_code == 200:
                        return resp.text
                except Exception as e:
                    logger.info(e)
                    pass
                max_try += 1
                if max_try > 5:
                    return ""
                src_url = random.choice(self.src_urls)

    def parse(self, response_text, k=5):
        if not response_text:
            return ""
        html = etree.HTML(response_text)
        # answer = html.xpath('//div[@class="answer"]/span/text()')
        # answer = '\n'.join(answer)
        # if answer:
        #     return answer
        articles = html.xpath('//div[@id="urls"]/article/p[@class="content"]')
        snipets = set()
        for art in articles:
            s = (
                etree.tostring(art, encoding="utf-8", method="text")
                .decode("utf-8")
                .strip()
            )
            if s:
                snipets.add(f"- {s}")
        snipets = "\n".join(list(snipets)[:k])
        return snipets


if __name__ == "__main__":
    import asyncio

    engine = SearxSearch()

    query = "gold price today"
    res = asyncio.run(engine.a_search(query))
    logger.info(res)
