import io
import json
import asyncio
import shutil
from typing import Type, List, Literal
from pathlib import Path


# local module
from utils.logger import logger
from utils.helpers import generate_sha256, bytes_to_b64
from utils.file_convert import to_pdf
from utils.storage.minio_storage import MINIO_STORAGE
from utils.storage.shelve_storage import JsonStorage
from base_agent.async_agent import AsyncAgent
from customized_agent.data_analyzer.prompt_template import (
    BaseTemplate,
    Classification,
    SubCategory,
    FormAnalysis
)
from customized_agent.data_analyzer.config import (
    AnalyzerTaskConfig,
    SHELVE_CONFIG,
    ANALYZER_CONFIG,
    FORM_ANALYZER_CONFIG,
    TASK_CONFIG,
    OCR_CONFIG,
    DATATYPE_MAP
)
from module.toolkit.ai_tools import OcrApi


class DataAnalyzer:
    """
    A state free agent used to parse and analyze in-vitro/in-vivo diagnostics result.
    """
    def __init__(self, config: AnalyzerTaskConfig = None) -> None:
        self.config = config or TASK_CONFIG
        # Create minio storage. TODO: Use IPFS storage
        self.create_bucket()
        # Initiate Router and Peter Chatbot agents
        self.analyzer = AsyncAgent(ANALYZER_CONFIG)
        self.form_analyzer = AsyncAgent(FORM_ANALYZER_CONFIG)
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
        self, prompt: str, sys_prompt: str, is_received: bool = True, history: list = None
    ):
        history = history or [{
            'role': 'system',
            'content': sys_prompt
        }]
        message = dict(role="user" if is_received else "assistant", content=prompt)
        history.append(message)
        return history


    async def chat_once_pipe(self, sys_prompt: str, template_cls: Type[BaseTemplate], template_kw: dict):
        template = template_cls(**template_kw)
        prompt = template.format_template()
        history = self.construct_history(prompt, sys_prompt)
        res = await self.analyzer.chat_once_pure(history, temperature=self.config.temperature)
        res = template.extract(res)
        return res


    def create_bucket(self):
        # Initialize the minio storage bucket
        MINIO_STORAGE.create_bucket(self.config.bucket)


    async def get_minio_data(self, obj_name: str):
        bucket = self.config.bucket
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
        # Read the OCR markdown result from the cache
        cache = Path(self.config.ocr_cache)
        md_path = cache.joinpath(f'{data_path_hash}/{data_path_hash}.md')
        with open(str(md_path), 'r') as f:
            data = f.read()
        return data
        

    async def parse_data(
        self, 
        data: bytes, 
        data_path_hash: str, 
        data_type: Literal["image/jpeg",
            "image/png",
            "application/pdf",
            "text/markdown",
            "text/plain"]
    ) -> str:
        """Parse the data to the standard markdown format.

        Args:
            data (bytes): The data to be parsed.
            data_path_hash (str): The hash of the data path.
            data_type (str): The type of the data.
        """
        # Get standard data_type
        data_type = DATATYPE_MAP.get(data_type, None)
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


    async def move_parsed_data(self, data: str, user_id: str, data_path_hash:str):
        """Move the parsed data to the minio storage.

        Args:
            data (str): The parsed data.
            user_id (str): The user id.
            data_path_hash (str): The hash of the data path.
        """
        if self.config.use_ipfs:
            raise NotImplementedError('IPFS storage is unsupported now.')
        else:
            await asyncio.to_thread(
                MINIO_STORAGE.put_object,
                # Construct the parsed file's oject_name
                f'{self.config.version}/{user_id}/parsed/{data_path_hash}.md',
                io.BytesIO(data.encode()),
                self.config.bucket
            )
        # Free cache
        cache = self.config.ocr_cache
        output_dir = cache.joinpath(data_path_hash)
        if output_dir.exists():
            shutil.rmtree(str(output_dir))
        logger.info(f'Cache free: {data_path_hash}')


    async def receive_data(self, storage_type: str, data_type: str, data_path: str, user_id: str) -> str:
        """Receive the data from the storage and parse it to the standard markdown format.

        Args:
            storage_type (str): The type of the storage.
            data_type (str): The type of the data.
            data_path (str): The path of the data.
            user_id (str): The user id.
        """
        data = await self.get_data(storage_type, data_path)
        data_path_hash = generate_sha256(data_path)
        data = await self.parse_data(data, data_path_hash, data_type)
        await self.move_parsed_data(data, user_id, data_path_hash)
        return data_path_hash


    async def get_major_cate(self, diagno_md: str) -> dict:
        """Get the major diagnostics categories from the database.

        Args:
            diagno_md (str): The markdown format of the diagnostics result.
        """
        categories = self.cate_db.item_list_md()
        if not categories:
            categories = 'Not provided.'
        res = await self.chat_once_pipe(
            self.analyzer.config.sys_prompt, 
            Classification, 
            dict(major_cate=categories, diagno_res=diagno_md)
        )
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
        """Analyze the sub-item diagnostics categories from the database.

        Args:
            major_cate (str): The major diagnostics category.
            cate_info (str): The markdown format of the diagnostics result.
        """
        major_cate = major_cate.title()
        sub_items = self.cate_db.item_list_md([major_cate])
        if not sub_items:
            sub_items = 'Not provided.'
        res = await self.chat_once_pipe(
            self.analyzer.config.sys_prompt,
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
        """Generate the analysis result from the major diagnostics categories.

        Args:
            major_cate_info (List[dict]): The major diagnostics categories.
        """
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
        """Analyze the diagnostics result.

        Args:
            diagno_md (str): The markdown format of the diagnostics result.
        """
        major_cates = await self.get_major_cate(diagno_md)
        analysis_res = await self.generate_analysis(major_cates)
        return analysis_res


    async def analyze_data(self, user_id: str, data_path_hash: str):
        """Analyze the parsed data.

        Args:
            user_id (str): The user id.
            data_path_hash (str): The hash of the data path.
        """
        diagno_md = await asyncio.to_thread(
            MINIO_STORAGE.get_object, 
            f'{self.config.version}/{user_id}/parsed/{data_path_hash}.md', 
            self.config.bucket
        )
        diagno_md = diagno_md.decode()
        analysis_res = await self.analyze(diagno_md)
        await asyncio.to_thread(
            MINIO_STORAGE.put_object,
            # Construct the parsed file's oject_name
            f'{self.config.version}/{user_id}/final/{data_path_hash}.json',
            analysis_res,
            self.config.bucket
        )
        return analysis_res


    async def analyze_questionnaire(self, user_id:str, data_path_hash: str):
        """Analyze the questionnaire.

        Args:
            user_id (str): The user id.
            data_path_hash (str): The hash of the data path.
        """
        questionnaire = await asyncio.to_thread(
            MINIO_STORAGE.get_object, 
            f'{self.config.version}/{user_id}/parsed/{data_path_hash}.md', 
            self.config.bucket
        )
        questionnaire = questionnaire.decode()
        analysis_res = await self.chat_once_pipe(
            self.form_analyzer.config.sys_prompt, 
            FormAnalysis, 
            dict(questionnaire=questionnaire)
        )
        await asyncio.to_thread(
            MINIO_STORAGE.put_object,
            # Construct the parsed file's oject_name
            f'{self.config.version}/{user_id}/final/{data_path_hash}.json',
            analysis_res,
            self.config.bucket
        )
        return analysis_res


    async def analyze_file(self, file_name: str, file_type: str, file_bytes: bytes):
        """Analyze the uploaded diagnostics raw file.

        Args:
            file_name (str): The name of the file.
            file_type (str): The type of the file.
            file_bytes (bytes): The bytes of the file.
        """
        data_path_hash = generate_sha256(file_name)
        data = await self.parse_data(file_bytes, data_path_hash, file_type)
        analysis_res = await self.analyze(data)
        return analysis_res



if __name__ == '__main__':
    ...