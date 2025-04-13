import json
import re
import copy
import asyncio
import shutil
import img2pdf
from typing import Type, List, Literal
from pathlib import Path


# local module
from utils.logger import logger
from utils.helpers import generate_sha256, bytes_to_b64, b64_to_bytes
from utils.file_convert import to_pdf
from utils.storage.minio_storage import MINIO_STORAGE
from utils.storage.shelve_storage import JsonStorage
from base_agent.async_agent import AsyncAgent
from customized_agent.data_analyzer.prompt_template import (
    BaseTemplate,
    Classification,
    SubCategory
)
from customized_agent.data_analyzer.config import (
    AnalyzerTaskConfig,
    SHELVE_CONFIG,
    ANALYZER_CONFIG,
    TASK_CONFIG,
    OCR_CONFIG
)
from module.toolkit.ai_tools import OcrApi


class DataAnalyzer:
    def __init__(self, config: AnalyzerTaskConfig = None) -> None:
        self.config = config or TASK_CONFIG
        # Create minio storage. TODO: Use IPFS storage
        self.create_bucket()
        # Initiate Router and Peter Chatbot agents
        self.analyzer = AsyncAgent(ANALYZER_CONFIG)
        # Initiate diagnostics category database, which has schema like:
        '''
        {
            "major_category_0": {
                "sub_category_0": {
                    "definition": ...
                    "explanation": ...
                },
                "sub_category_1": {...},
                ...
            },
            ...
        }
        '''
        self.cate_db = JsonStorage(SHELVE_CONFIG)

    
    def construct_history(
        self, prompt: str, is_received: bool = True, history: list = None
    ):
        history = history or [{
            'role': 'system',
            'content': self.analyzer.config.sys_prompt
        }]
        message = dict(role="user" if is_received else "assistant", content=prompt)
        history.append(message)
        return history


    async def chat_once_pipe(self, template_cls: Type[BaseTemplate], template_kw: dict):
        template = template_cls(**template_kw)
        prompt = template.format_template()
        history = self.construct_history(prompt)
        res = await self.analyzer.chat_once_pure(history, temperature=0.2)
        res = template.extract(res)
        return res


    def create_bucket(self):
        MINIO_STORAGE.create_bucket(self.config.diag_bucket)
        MINIO_STORAGE.create_bucket(self.config.parsed_bucket)


    async def get_minio_data(self, obj_name: str):
        bucket = self.config.diag_bucket
        data_bytes = await asyncio.to_thread(MINIO_STORAGE.get_object, obj_name, bucket)
        return data_bytes
    

    async def get_ipfs_data(self, key: str):
        raise NotImplementedError('IPFS storage is unsupported now.')


    async def get_data(self, storage_type: str, data_path: str) -> bytes:
        if storage_type == 'minio':
            data = await self.get_minio_data(data_path)
        elif storage_type == 'ipfs':
            data = await self.get_ipfs_data(data_path)
        else:
            raise NotImplementedError(f'Unsupported storage type: {storage_type}')
        return data


    async def parse_pdf(self, pdf_bytes:bytes, data_path_hash:str):
        """Request the remote OCR service to obtain the pdf's layout result.

        Args:
            pdf_bytes (bytes): PDF file bytes.
            data_path_hash (str): PDF object_path's md5 hash, used to identify the unique file
        """
        ocr = OcrApi(OCR_CONFIG)
        pdf_bs64 = bytes_to_b64(pdf_bytes)
        await ocr.send_ocr(pdf_bs64, data_path_hash, self.config.ocr_api)

    
    def read_ocr(self, data_path_hash) -> str:
        cache = Path(self.config.ocr_cache)
        md_path = cache.joinpath(f'{data_path_hash}/{data_path_hash}.md')
        with open(str(md_path), 'r') as f:
            data = f.read()
        return data
        

    async def parse_data(
        self, 
        data: bytes, 
        data_path_hash: str, 
        data_type: Literal['text', 'pdf', 'img']
    ) -> str:
        if data_type == 'text':
            content = data.decode()
        elif data_type == 'img':
            data = await asyncio.to_thread(to_pdf, data)
            await self.parse_pdf(data, data_path_hash)
            content = await asyncio.to_thread(self.read_ocr, data_path_hash)
        elif data_type == 'pdf':
            await self.parse_pdf(data, data_path_hash)
            content = await asyncio.to_thread(self.read_ocr, data_path_hash)
        else:
            raise NotImplementedError(f'Unsupported data type: {data_type}')
        return content


    async def move_parsed_data(self, data: str, data_path_hash:str):
        if self.config.use_ipfs:
            raise NotImplementedError('IPFS storage is unsupported now.')
        else:
            await asyncio.to_thread(
                MINIO_STORAGE.put_object,
                f'{self.config.version}/{data_path_hash}.md',
                data.encode(),
                self.config.parsed_bucket
            )
        # Free cache
        cache = self.config.ocr_cache
        output_dir = cache.joinpath(data_path_hash)
        shutil.rmtree(str(output_dir))
        logger.info(f'Cache free: {data_path_hash}')


    async def receive_data(self, storage_type: str, data_type: str, data_path: str) -> str:
        data = await self.get_data(storage_type, data_path)
        data_path_hash = generate_sha256(data_path)
        data = await self.parse_data(data, data_path_hash, data_type)
        return data_path_hash


    async def get_major_cate(self, diagno_md: str) -> dict:
        categories = self.cate_db.item_list_md()
        if not categories:
            categories = 'Not provided.'
        res = await self.chat_once_pipe(Classification, dict(major_cate=categories, diagno_res=diagno_md))
        # Update the diagnostics category database, 
        # create the new major diagnostics category.
        created = res.get('newly_created', None)
        if created:
            upsert_data = []
            for item in created:
                upsert_data.append(([item['name'].title()], dict()))
            self.cate_db.batch_upsert(upsert_data)
        return [value for _, values in res.items() for value in values]


    async def analyze_sub_item(self, major_cate: str, cate_info: str):
        major_cate = major_cate.title()
        sub_items = self.cate_db.item_list_md([major_cate])
        if not sub_items:
            sub_items = 'Not provided.'
        res = await self.chat_once_pipe(
            SubCategory, 
            dict(major_cate=major_cate, sub_items=sub_items, diagno_res=cate_info)
        )
        # Update the sub-item category database, 
        # create the new sub-item diagnostics category.
        created = res.get('newly_created', [])
        if created:
            upsert_data = []
            for item in created:
                upsert_data.append((
                    [major_cate, item['name']], 
                    {'definition': item['definition'], 'explanation': item['explanation']}
                ))
            self.cate_db.batch_upsert(upsert_data)
        provided = res.get('provided', [])
        sub_items = provided + created
        for item in sub_items:
            item['name'] = item['name'].upper()
        return {major_cate: sub_items}


    async def generate_analysis(self, major_cate_info: List[dict]) -> dict:
        tasks = []
        for item in major_cate_info:
            cate = item['name'].title()
            info = item['information']
            tasks.append(asyncio.create_task(self.analyze_sub_item(cate, info)))
        results = await asyncio.gather(*tasks)
        final_res = dict()
        for res in results:
            final_res.update(res)
        return final_res


    async def analyze(self, diagno_md: str):
        major_cates = await self.get_major_cate(diagno_md)
        analysis_res = await self.generate_analysis(major_cates)
        return analysis_res


    async def analyze_data(self, data_path_hash):
        diagno_md = await asyncio.to_thread(
            MINIO_STORAGE.get_object, 
            f'{self.config.version}/{data_path_hash}.md', 
            self.config.parsed_bucket
        )
        diagno_md = diagno_md.decode()
        analysis_res = await self.analyze(diagno_md)
        return analysis_res
        

if __name__ == '__main__':
    analyzer = DataAnalyzer()
    
    md_path = '/root/rag/longevity-agents/.cache/ocrs/Hormones/732c08928ac5f308297146dc30bb1602.md'
    with open(md_path, 'r') as f:
        md = f.read()
    
    async def main():
        res = await analyzer.analyze(md)
        return res

    res = asyncio.run(main())
    with open('/root/rag/longevity-agents/customized_agent/data_analyzer/dev/results_hormones.json', 'w') as f:
        json.dump(res, f, indent=4)
    ...