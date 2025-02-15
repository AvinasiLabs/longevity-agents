import os
import asyncio
import serpapi

# local module
from configs.config import SerpapiConfig, SERPAPI_CONFIG


class SerpApi:
    def __init__(self, config:SerpapiConfig=None):
        self.config = config or SERPAPI_CONFIG

    
    async def search(self, query):
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.config.token,
            "location": self.config.location,
            'gl': self.config.gl,
            'hl': self.config.hl
        }

        results = await asyncio.to_thread(serpapi.search, params)
        organic_results = results["organic_results"]
        snippet_template = '{}. {} - {}'
        agg_results = ''
        for i, res in enumerate(organic_results):
            snippet = snippet_template.format(i + 1, res['title'], res['snippet'])
            agg_results = f'{agg_results}{snippet}\n'
        return agg_results
    

if __name__ == '__main__':
    serp = SerpApi()

    query = 'sushi'
    res = serp.search(query)
    print(res)
    ...