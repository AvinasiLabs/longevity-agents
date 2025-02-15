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

# local module
from utils.helpers import open_yaml_config


GLOBAL_CONFIG_FP = Path(__file__).parent.parent.joinpath("assets/global_config.yaml")
GLOBAL_CONFIG = open_yaml_config(str(GLOBAL_CONFIG_FP))


class AgentConfig(BaseSettings):
    """
    LLM must be compatible with OpenAI API
    """

    # config setting
    model_config: SettingsConfigDict = SettingsConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8"
    )
    # config
    client_type: Optional[str] = "openai"
    llm_token: Optional[str] = None
    llm_uri: Optional[str] = None
    llm_model: Optional[str] = None
    sys_prompt: str = "You are a helpful assistant."
    max_token: int = 256


class DingDingBotConfig(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8"
    )

    url: str = ""
    user_phone: Union[str, List[str]] = ""
    user_id: Union[str, List[str]] = ""
    secret: str = ""
    is_send_all: bool = False


class WechatEnterpriseConfig(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8"
    )

    url: str = ""


class FrontEndConfig(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="frontend_",
    )

    host: str = ""
    port: str = ""
    news_analysis_api: str = "api/news/analysis"
    token: str = ""


class TelegramConfig(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8"
    )

    chat_id: int = 0
    token: str = ""


class MessengerConfig(BaseSettings):
    dingding_messenger: Dict[str, DingDingBotConfig] = {
        "default_bot": DingDingBotConfig()
    }
    wechat_messenger: Dict[str, WechatEnterpriseConfig] = {
        "default_bot": WechatEnterpriseConfig()
    }
    frontend_messenger: FrontEndConfig = FrontEndConfig()
    telegram_messenger: TelegramConfig = TelegramConfig()


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

    proxy: ProxyConfig = ProxyConfig(**GLOBAL_CONFIG["proxy"])
    host: str = "127.0.0.1"
    port: int = 9527
    api_map: dict = dict()


class BinanceDataCollectorConfig(BaseSettings):
    api: dict
    data_setting: dict
    proxy: ProxyConfig = ProxyConfig()


class MongoConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_prefix="mongo_"
    )

    conn_str: str = ""
    db_name: str = "AI_News"
    coll_name: str = "info_intelligence"


if __name__ == "__main__":
    ...
