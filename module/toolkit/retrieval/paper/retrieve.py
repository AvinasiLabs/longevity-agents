import asyncio
import heapq
import pickle
import re
from pathlib import Path
from typing import List
from urllib.parse import urljoin
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed


# Local modules
from utils.helpers import fetch, generate_md5
from configs.config_cls import RetrievalConfig
from configs.config import MAC
from module.toolkit.retrieval.paper.config import PAPER_RETRIEVAL_CONFIG


class PaperRetrieve:
    def __init__(self, config: RetrievalConfig = None):
        self.config = config or PAPER_RETRIEVAL_CONFIG
        self.semaphore = asyncio.Semaphore(self.config.semaphore)
        self.pool = ProcessPoolExecutor(self.config.max_workers)


    async def search(
        self,
        query:str, 
        domain:str,
        threshold=0.3, 
        topk=10
    ):
        """Call the retrieval API, find documents that match the query in certain conditions.

        Args:
            query (str): Query text.
            domain (str, optional): Knowledge base name
            threshold (float, optional): Similarity threshold for vector retrieval, 0 <= threshold <= 1.
            topn (int, optional): topn most related result for each of vector retrieval and BM25 retrieval. 

        Returns:
            List[dict]: For example:
                [
                    {'text': 'xxxxx',
                    'index': 92,
                    'file_name': 'sample0513.pdf',
                    'url': 'images/page67_image0.jpg'},
                    {'text': 'xxxxx',
                    'index': 90,
                    'file_name': 'sample7833.pdf',
                    'url': ''},
                    ...
                ]
        """
        url = urljoin(self.config.endpoint, self.config.retrieve_api)
        body = {
            'domain': domain,
            'query': query,
            'threshold': threshold,
            'topk': topk,
            # TODO: 由于数据集的字段可能不一致，需要重新设计LLM输入结构
            'csid': MAC
        }
        resp = await fetch(url, data=body, cls_name='PaperRetrieve', timeout=300, semaphore=self.semaphore)
        return resp['result']
    

    def parse(self, documents:List[dict], domain:str, endpoint:str):
        result = defaultdict(list)
        url_map = dict()
        index = 0
        for record in documents:
            file_name = record['file_name']
            index = record['agg_index']
            text = record['text']
            # Replace url
            file_md5 = generate_md5(Path(file_name).stem)
            raw_urls = re.findall(r"images/[a-fA-F0-9]{64}\.jpg", text)
            img_md5s = re.findall(r"images/([a-fA-F0-9]{64})\.jpg", text)
            new_urls = [f'{endpoint}/v1/storage/image?domain={domain}&file={file_md5}&image={image_md5}' for image_md5 in img_md5s]
            for i, url in enumerate(new_urls):
                url_sub = f'<image>{index}</image>'
                text = re.sub(raw_urls[i], url_sub, text)
                url_map[index] = url
                index += 1
            result[file_name].append((index, text))
        for k, v in result.items():
            result[k] = sorted(v)
            result[k] = '\n\n'.join([ele[1] for ele in v])

        template = '---\n**File Name**: {file_name}\n**Reference**:\n{text}\n---\n\n'
        result = [(file_name, template.format(file_name=file_name, text=text)) for file_name, text in result.items()]
        return result, url_map

    
    async def pipe(self, query:str, domain:str, endpoint:str):
        result = await self.search(query, domain, self.config.threshold, self.config.topk)
        result, url_map = self.parse(result, domain, endpoint)
        return result, url_map
    

if __name__ == '__main__':
    import asyncio
    import json


    retrieval = PaperRetrieve()

    domain = 'longevity_paper_2504'
    endpoint = 'http://127.0.0.1:8002'

    query = "How to evaluate the brain's age?"
    res = asyncio.run(retrieval.pipe(query, domain, endpoint))
    with open('/root/rag/longevity-agents/dev/answer.json', 'w') as f:
        json.dump(res, f, indent=4)
    print(res)
    ...