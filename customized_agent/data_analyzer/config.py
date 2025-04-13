import os
from pathlib import Path

# local module
from configs.config_cls import AgentConfig, TaskConfig, OcrConfig, ShelveConfig
from customized_agent.data_analyzer.prompt_template import (
    SYS_ROUTER, SYS_ANALYZER
)


RELATIVE_PATH = Path(__file__).parent
CACHE_DIR = RELATIVE_PATH.joinpath('.cache')
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class AnalyzerTaskConfig(TaskConfig):
    use_ipfs: bool = False
    ocr_api: str
    ocr_cache: Path = CACHE_DIR
    diag_bucket: str = None
    parsed_bucket: str = 'diagno-parsed'
    version: str = 'v1'


TASK_CONFIG = AnalyzerTaskConfig(
    use_ipfs=False,
    ocr_api='http://113.150.232.222:41041/v1/ocr',
    diag_bucket='diagno-raw',
    parsed_bucket='diagno-parsed',
    version='v1'
)


ROUTER_CONFIG = AgentConfig(
    llm_token=os.getenv('AIMLAPI_KEY'),
    llm_uri='https://api.aimlapi.com/v1',
    llm_model='gpt-4o',
    sys_prompt=SYS_ROUTER, 
    max_token=512
)


OCR_CONFIG = OcrConfig(
    base_url='http://127.0.0.1:48308/v1/ocr',
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


SHELVE_CONFIG = ShelveConfig(
    db_path=RELATIVE_PATH.joinpath('assets/diagno_category.json')
)

