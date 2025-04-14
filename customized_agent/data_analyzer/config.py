import os
from pathlib import Path
from pydantic import Field

# local module
from configs.config_cls import AgentConfig, TaskConfig, OcrConfig, ShelveConfig
from customized_agent.data_analyzer.prompt_template import (
    SYS_ANALYZER, SYS_FORM_ANALYZER
)


RELATIVE_PATH = Path(__file__).parent
CACHE_DIR = RELATIVE_PATH.joinpath('.cache')
CACHE_DIR.mkdir(parents=True, exist_ok=True)


OCR_API = 'http://173.185.79.174:44568/v1/ocr'


class AnalyzerTaskConfig(TaskConfig):
    use_ipfs: bool = False
    ocr_api: str
    ocr_cache: Path = CACHE_DIR
    bucket: str = 'diagnostic'
    version: str = 'v1'
    temperature: float = Field(0.2, gt=0)


TASK_CONFIG = AnalyzerTaskConfig(
    use_ipfs=False,
    ocr_api=OCR_API,
    bucket='diagnostic',
    version='v1',
    temperature=0.2
)


OCR_CONFIG = OcrConfig(
    base_url=OCR_API,
    timeout=3600,
    sema_process=4,
    ocr_cache=CACHE_DIR
)


ANALYZER_CONFIG = AgentConfig(
    llm_token=os.getenv('AIMLAPI_KEY'),
    llm_uri='https://api.aimlapi.com/v1',
    # llm_model='gpt-4o-mini',
    llm_model='x-ai/grok-3-mini-beta',
    # llm_model='nvidia/llama-3.1-nemotron-70b-instruct',
    sys_prompt=SYS_ANALYZER,
    max_token=8192,
    temperature=0.01
)


FORM_ANALYZER_CONFIG = AgentConfig(
    llm_token=os.getenv('AIMLAPI_KEY'),
    llm_uri='https://api.aimlapi.com/v1',
    # llm_model='gpt-4o-mini',
    llm_model='x-ai/grok-3-mini-beta',
    # llm_model='nvidia/llama-3.1-nemotron-70b-instruct',
    sys_prompt=SYS_FORM_ANALYZER,
    max_token=8192,
    temperature=0.01
)


SHELVE_CONFIG = ShelveConfig(
    db_path=RELATIVE_PATH.joinpath('assets/diagno_category.json')
)


DATATYPE_MAP = {
    "image/jpeg": "img",
    "image/png": "img",
    "application/pdf": "pdf",
    "text/markdown": "text",
    "text/plain": "text",
}
