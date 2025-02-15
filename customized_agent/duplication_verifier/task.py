#! python3
# -*- encoding: utf-8 -*-
"""
@Time: 2024/05/11 11:20:35
@Author: Louis
@Version: 1.0
@Contact: lululouisjin@gmail.com
@Description: Used to verify if a newly received text is duplicated with history text in buffer or not.
"""


import numpy as np
from pathlib import Path
from collections import OrderedDict

# local module
from base_agent.agent import Agent, AgentConfig
from customized_agent.duplication_verifier.prompt_template import DropDuplicationTemplat
from utils.helpers import open_yaml_config, gen_md5
from utils.retrieve import VectorRetrieval
from utils.logger import logger
from collections import deque


ABS_PATH = Path(__file__).parent.parent.parent
CONFIG_FP = ABS_PATH.joinpath("customized_agent/duplication_verifier/config.yaml")
CONFIG = open_yaml_config(CONFIG_FP)
LLM_CONFIG = CONFIG["llm_config"]
EMB_CONFIG = CONFIG["embedding_config"]


class FixedSizedDict(OrderedDict):
    def __init__(self, max_size):
        super().__init__()
        self.max_size = max_size

    def __setitem__(self, key, value) -> None:
        if len(self) >= self.max_size:
            self.popitem(last=False)
        return super().__setitem__(key, value)


class DuplicationVerifier:
    def __init__(self, api_list: list) -> None:
        self.agent = Agent(AgentConfig(**LLM_CONFIG))
        self.retrieval = self.init_retrieval()
        self.embedding_buffer = np.zeros(
            (EMB_CONFIG["buffer_size"], EMB_CONFIG["dimensions"])
        )
        self.content_buffer = deque(maxlen=EMB_CONFIG["buffer_size"])
        self.fresh_buffer = FixedSizedDict(max_size=10000)
        self.api_list = api_list

    def init_retrieval(self):
        """Initiate the vector retrieval, which is used to find the semantic similar content.

        Returns:
            VectorRetrieval: The VectorRetrieval instance used for vector retrieval.
        """
        retrieval = VectorRetrieval(
            api_key=EMB_CONFIG["api_key"],
            base_url=EMB_CONFIG["base_url"],
            model=EMB_CONFIG["model"],
            dimensions=EMB_CONFIG["dimensions"],
        )
        return retrieval

    def insert_buffer(self, embedding, content):
        self.embedding_buffer[1:] = self.embedding_buffer[:-1]
        self.embedding_buffer[0] = embedding
        self.content_buffer.appendleft(content)

    def is_duplicated(self, news, api_name):
        # Verify if a new-coming news is in self.fresh_buffer
        news_md5 = gen_md5(news)
        if news_md5 not in self.fresh_buffer:
            self.fresh_buffer[news_md5] = {
                "is_duplicated": False,
                "api_set": {api_name},
            }
        else:
            is_same_api = (
                True if api_name in self.fresh_buffer[news_md5]["api_set"] else False
            )
            self.fresh_buffer[news_md5]["api_set"].add(api_name)
            is_dup = self.fresh_buffer[news_md5]["is_duplicated"]
            if len(self.fresh_buffer[news_md5]["api_set"]) == len(self.api_list):
                self.fresh_buffer[news_md5]["is_duplicated"] = True
            return True if is_same_api else is_dup
        is_dup, news_emb, score = self.retrieval.is_semantic_dup(
            news,
            self.embedding_buffer,
            accept_threshold=EMB_CONFIG["accept_threshold"],
            reject_threshold=EMB_CONFIG["reject_threshold"],
        )
        if is_dup == "Unknown":
            is_dup = self.is_duplicated_ambi(news, score)
        if is_dup == "Yes":
            self.fresh_buffer[news_md5]["is_duplicated"] = True
            return True
        elif is_dup == "No":
            self.insert_buffer(news_emb, news)
            return False

    def is_duplicated_ambi(self, news, score):
        """Use LLM to identify if the ambiguous news is similar with each other or not.

        Args:
            news (str): The target news that compares with source news
            score (np.ndarray): Similarity score between target news and all source news

        Returns:
            bool: True for duplicated, false for not.
        """
        v_3, id_3 = self.retrieval.topk(score, k=3)
        src_news = ""
        for i, v in enumerate(v_3):
            index = id_3[i]
            if v > EMB_CONFIG["reject_threshold"]:
                src_news += f"- {self.content_buffer[index]}\n"
        template = DropDuplicationTemplat(target_news=news, source_news=src_news)
        prompt = template.format_template()
        try:
            content = self.agent.chat_once(prompt, stop=[",", "."])
            return template.extract(content)
        except Exception as e:
            logger.info(e)
            return "No"


if __name__ == "__main__":
    ...
