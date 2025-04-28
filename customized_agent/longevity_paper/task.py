import json
import re
import copy
import asyncio
from typing import List


# local module
from utils.logger import logger
from utils.helpers import process_generators
from base_agent.async_agent import AsyncAgent
from base_agent.a_stream_agent import AStreamAgent
from customized_agent.longevity_paper.prompt_template import (
    QueryAnalysis,
    ReferenceTemplate,
    SYS_ROUTER,
    SYS_PAPER
)
from customized_agent.longevity_paper.config import (
    PaperTaskConfig,
    ROUTER_CONFIG,
    PAPER_CONFIG,
    TASK_CONFIG,
    MYSQL_TABLE
)
from module.toolkit.search_tools.serp_api import SerpApi
from module.toolkit.retrieval.paper.retrieve import PaperRetrieve
from utils.storage.mysql import MYSQL_STORAGE

class PaperChatbot:
    def __init__(self, config: PaperTaskConfig = None) -> None:
        self.config = config or TASK_CONFIG
        # Initiate Router and Peter Chatbot agents
        self.init_agent()
        # Initiate knowledge
        self.full_history = [{'role': 'system', 'content': self.paper.config.sys_prompt}]
        self.lite_history = [{'role': 'system', 'content': self.paper.config.sys_prompt}]


    def init_agent(self):
        # initiate agents
        self.paper = AStreamAgent(PAPER_CONFIG)
        self.router = AsyncAgent(ROUTER_CONFIG)
        self.tool_caller = AStreamAgent(PAPER_CONFIG)

        # initate tools
        # Web search
        self.search_engine = SerpApi()
        params = {
            "query": {
                "type": "string",
                "description": 'keywords in original question for google search, you may need optimize them for Google search to satisfy your demand. Must be dict. Search for general information and no add "site" parameter'
            }
        }
        # Paper retrieve
        self.retrieval = PaperRetrieve()
        
        # add tools
        self.tool_caller.register_tool(
            name="Search Engine",
            description="The Google search engine, you can use it to search information on the Internet if needed.",
            params=json.dumps(params),
            func=self.search_engine.search,
        )


    async def retrieve_or_not(self, question):
        """Infer the user's intention. Identify the topic."""
        rc = self.router.round_chat(
            sys_prom=self.router.config.sys_prompt
        )
        template = QueryAnalysis(question=question)
        prompt = template.format_template()
        res = await rc(prompt, max_tokens=self.router.config.max_token)
        label = template.extract(res)
        return label
    

    async def retrieve(self, query:str):
        result, url_map = await self.retrieval.pipe(
            query, 
            self.config.domain,
            self.config.image_endpoint
        )
        # Keep the top <retrieval_keep> references
        result = result[:self.config.retrieval_keep]
        # Replace the image url

        return result, url_map
    
    
    async def answer_with_ref(self, question:str, file_name:str, ref:str):
        template = ReferenceTemplate(question=question, ref=ref)
        prompt = template.format_template()
        resp = await self.paper.chat_once(prompt, temperature=self.paper.config.temperature)
        result = ''
        on_going = False
        has_answer = False
        async for chunk in resp:
            choices = chunk.choices
            if choices:
                chunk = choices[0].delta.content
                if has_answer or re.findall(r'Final Answer[\s\S]*?\n', result, re.I):
                    has_answer = True
                    if not on_going:
                        yield f'## **Reference**: {file_name}\n'
                        on_going = True
                    yield chunk
                elif 'Call tools' in result:
                    return
                if not has_answer and chunk:
                    result = f'{result}{chunk}'
        ...


    async def parallel_answer(self, question:str, refs:List[str]):
        pending = []
        files = []
        for ref in refs:
            pending.append(self.answer_with_ref(question, ref[0], ref[1]))
            files.append(ref[0])

        result = ''
        async for _, chunk in process_generators(*pending):
            if chunk is None:
                delta = '\n\n'
            else:
                delta = chunk
            yield delta
            result = f'{result}{delta}'
        self.full_history.append({'role': 'assistant', 'content': result})
        

    async def tool_answer(self, question:str, history:list):
        self.full_history.append({'role': 'user', 'content': question})
        tool_names = list(self.tool_caller.toolkit.keys())
        result = self.tool_caller.tool_call_chat(
            question=question,
            history=history,
            temperature=self.tool_caller.config.temperature,
            tool_names=tool_names
        )
        content = ''
        async for chunk in result:
            content = f'{content}{chunk}'
            yield chunk
        self.full_history.append({'role': 'assistant', 'content': content})
    

    async def pipe(self, question: str, session_id: str = ''):
        history = MYSQL_STORAGE.query_all(f"select * from {MYSQL_TABLE} where session_id = '{session_id}' order by insert_time asc limit 10")
        history = [{'role': 'user' if item['sender'] == 0 else 'assistant', 'content': item['content']} for item in history]
        self.lite_history = [{'role': 'system', 'content': self.paper.config.sys_prompt}] + history
        self.full_history = copy.deepcopy(self.lite_history)
        self.lite_history.append({'role': 'user', 'content': question})
        # Decide to use retrieval tool or not
        label = await self.retrieve_or_not(question)
        # streaming answer with knowledge base
        if label == 'GENERAL':
            temp_history = copy.deepcopy(self.full_history)
            temp_history[0] = {'role': 'system', 'content': self.tool_caller.config.sys_prompt}
            result = self.tool_answer(question, temp_history)
            async for chunk in result:
                if chunk is not None:
                    yield chunk
        else:
            self.full_history.append({'role': 'user', 'content': question})
            # Retrieve paper knowledge
            refs, url_map = await self.retrieve(question)
            # Parallelly generate answers by paper
            result = self.parallel_answer(question, refs)
            temp = ''
            async for chunk in result:
                if chunk is not None:
                    temp = f'{temp}{chunk}'
                    if len(temp) > 8:
                        if '<' not in temp:
                            yield temp
                            temp = ''
                        elif re.findall(r'<[\s\S]{5}', temp):
                            index_str = re.search(r'<image>(\d+)?</image>', temp)
                            if not index_str:
                                if '<image' not in temp:
                                    yield temp
                                    temp = ''
                            else:
                                index = index_str.group(1)
                                if index:
                                    index = int(index)
                                    temp = re.sub(index_str.group(), f'![]({url_map[index]})', temp)
                                    yield temp
                                    temp = ''
                                else:
                                    temp = re.sub(index_str.group(), '', temp)
                                    yield temp
                                    temp = ''
                        else:
                            continue
        self.lite_history.append(copy.deepcopy(self.full_history[-1]))
        ...


if __name__ == '__main__':
    ...
