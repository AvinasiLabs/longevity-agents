import asyncio
import ssl
import aiohttp
from urllib.parse import urljoin


# Local module
from configs.config_cls import IPFSConfig
from configs.config import IPFS_CONFIG
from utils.helpers import bytes_to_b64, b64_to_bytes


class IPFSStorage:
    def __init__(self, config: IPFSConfig = None):
        self.config = config or IPFS_CONFIG
        self.semephore = asyncio.Semaphore(self.config.semaphore)
        self.init_session()


    def init_session(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout, **self.config.session_kw)


    async def __aenter__(self):
        return self
    

    async def __aexit__(self):
        self.session.close()


    async def update_data(self, key: str, value: str):
        api = urljoin(self.config.endpoint, f'/data/{key}')
        body = {'value': value}
        try:
            async with self.semephore:
                async with self.session.put(api, json=body) as resp:
                    res = await resp.json()
            return res
        except Exception as err:
            raise err


    async def get_data(self, key: str):
        api = urljoin(self.config.endpoint, f'/data/{key}')
        try:
            async with self.semephore:
                async with self.session.get(api) as resp:
                    res = await resp.json()
            return res
        except Exception as err:
            raise err


    async def delete_data(self, key: str):
        api = urljoin(self.config.endpoint, f'/data/{key}')
        try:
            async with self.semephore:
                async with self.session.delete(api) as resp:
                    res = await resp.json()
            return res
        except Exception as err:
            raise err
        

    def close(self):
        self.session.close()


if __name__ == '__main__':
    async def main():
        fp = '/root/rag/longevity-agents/dev/image.png'
        with open(fp, 'rb') as f:
            img = f.read()
        img_b64 = bytes_to_b64(img)

        key = 'louis_test/image.pgn'
        async with IPFSStorage() as ipfs:
            res = await ipfs.update_data(key, img_b64)
            print(res)
            res = await ipfs.get_data(key)
            ...


    asyncio.run(main())