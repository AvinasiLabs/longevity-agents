import os

# local module
from configs.config_cls import AgentConfig, TaskConfig
from customized_agent.longevity_paper.prompt_template import (
    SYS_ROUTER,
    SYS_PAPER
)


class PaperTaskConfig(TaskConfig):
    domain: str
    image_endpoint: str
    retrieval_keep: int = 5




TASK_CONFIG = PaperTaskConfig(
    domain='longevity_paper_2504',
    image_endpoint='http://10.11.148.250:8002',
    retrieval_keep=5
)


ROUTER_CONFIG = AgentConfig(
    llm_token=os.getenv('AIMLAPI_KEY'),
    llm_uri='https://api.aimlapi.com/v1',
    llm_model='gpt-4o',
    sys_prompt=SYS_ROUTER, 
    max_token=512
)


PAPER_CONFIG = AgentConfig(
    llm_token=os.getenv('AIMLAPI_KEY'),
    llm_uri='https://api.aimlapi.com/v1',
    # llm_model='gpt-4o-mini',
    # llm_model='x-ai/grok-beta',
    llm_model='nvidia/llama-3.1-nemotron-70b-instruct',
    sys_prompt=SYS_PAPER,
    max_token=65384,
    temperature=0.01
)

