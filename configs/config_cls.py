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
from pydantic import Field, SecretStr


BASE_PATH = Path(__file__).parent.parent


# Initiate cache directory
CACHE = BASE_PATH.joinpath('.cache')


# Initiate OCR cache directory
OCR_CACHE = CACHE.joinpath('ocrs')
OCR_CACHE.mkdir(parents=True, exist_ok=True)


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


class OcrConfig(BaseSettings):
    base_url: str
    timeout: float = 3600
    sema_process: int = 4  
    ocr_cache: Path = OCR_CACHE


class EmbeddingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='allow', env_prefix='emb_')

    emb_type: Literal['restapi', 'openai'] = 'openai'
    base_url: str
    timeout: float = 1800
    api: str = '/v1/embeddings'
    semaphore: int = 16
    model:str = ''
    batch_size: int = 128
    token: SecretStr = ''


class MongoConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_prefix="mongo_"
    )

    conn_str: str
    db_name: str
    coll_name: str


class MinioConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_prefix='minio_')


    host: str
    port: int
    ak: SecretStr
    sk: SecretStr
    bucket: str = None
    max_workers: int = 32


class IPFSConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_prefix="ipfs_"
    )

    endpoint: str
    semaphore: int = 4
    timeout: int = 300
    session_kw: dict = dict()


class MySQLConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_prefix="mysql_"
    )

    host: str
    port: int
    user: str
    pwd: SecretStr
    database: str
    charset: str = "utf8mb4"


class ShelveConfig(BaseSettings):
    db_path: Path


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
