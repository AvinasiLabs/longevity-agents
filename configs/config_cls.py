#! python3
# -*- encoding: utf-8 -*-
"""
@Time: 2024/04/16 13:42:23
@Author: Louis
@Version: 1.0
@Contact: lululouisjin@gmail.com
@Description: 
"""


from pathlib import Path
from typing import Literal, Union, Optional, Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class AgentConfig(BaseSettings):
    """
    LLM must be compatible with OpenAI API
    """

    # config setting
    model_config: SettingsConfigDict = SettingsConfigDict(
        extra="allow", env_file=".env", env_file_encoding="utf-8"
    )
    # config
    client_type: Optional[str] = "openai"
    llm_token: Optional[str] = None
    llm_uri: Optional[str] = None
    llm_model: Optional[str] = None
    sys_prompt: str = "You are a helpful assistant."
    max_token: int = 8000
    temperature: float = 0.2


class ProxyConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    is_used: bool = False
    is_static: bool = True
    host: str = "127.0.0.1"
    port: int = 26003
    api: str = ""


class RetrievalConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_prefix="retrieval_"
    )

    endpoint: str
    retrieve_api: str
    embedding_api: str = ''
    semaphore: int = 200
    max_workers: int = 4
    threshold: float = 0.8
    topk: int = 10


class MongoConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_prefix="mongo_"
    )

    conn_str: str
    db_name: str
    coll_name: str


class SerpapiConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_prefix="serpapi_"
    )

    token: str
    location: str    # Parameter defines from where you want the search to originate.
    gl: str = Field('us', description="Parameter defines the country to use for the Google search. It's a two-letter country code. (e.g., us for the United States, uk for United Kingdom, or fr for France). ")
    hl: str = Field('en', description="Parameter defines the language to use for the Google search. It's a two-letter language code. (e.g., en for English, es for Spanish, or fr for French).")


class TaskConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_prefix="task_"
    )


if __name__ == "__main__":
    ...
