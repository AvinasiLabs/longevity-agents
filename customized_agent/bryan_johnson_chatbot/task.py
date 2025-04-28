import json
import copy


# local module
from base_agent.async_agent import AsyncAgent
from base_agent.a_stream_agent import AStreamAgent
from customized_agent.bryan_johnson_chatbot.prompt_template import (
    QueryAnalysis,
    ReferenceTemplate,
    ToolCallingTemplate
)
from customized_agent.bryan_johnson_chatbot.config import (
    ROUTER_CONFIG,
    BRYAN_CONFIG,
    TOPICS_PATH,
    MYSQL_TABLE
)
from module.toolkit.search_tools.serp_api import SerpApi
from utils.storage.mysql import MYSQL_STORAGE


class BryanChatbot:
    def __init__(self) -> None:
        # Initiate Router and Bryan Chatbot agents
        self.init_agent()
        # Initiate knowledge
        self.init_topic_ref()
        self.full_history = [{'role': 'system', 'content': self.bryan.config.sys_prompt}]
        self.lite_history = [{'role': 'system', 'content': self.bryan.config.sys_prompt}]


    def init_agent(self):
        self.bryan = AStreamAgent(BRYAN_CONFIG)
        # register search engine tool
        self.search_engine = SerpApi()
        params = {
            "query": {
                "type": "string",
                "description": 'keywords in original question for google search, you may need optimize them for Google search to satisfy your demand. Must be dict. Search for general information and no add "site" parameter'
            }
        }
        self.bryan.register_tool(
            name="Search Engine",
            description="The Google search engine, you can use it to search information on the Internet if needed.",
            params=json.dumps(params),
            func=self.search_engine.search,
        )
        # TODO: register retriever tool
        
        self.router = AsyncAgent(ROUTER_CONFIG)
        self.tool_caller = AStreamAgent(BRYAN_CONFIG)
        self.tool_caller.register_tool(
            name="Search Engine",
            description="The Google search engine, you can use it to search information on the Internet if needed.",
            params=json.dumps(params),
            func=self.search_engine.search,
        )


    def init_topic_ref(self):

        def load_txt(fp):
            with open(fp, 'r') as f:
                topic = f.read()
            return topic
        
        self.topics = {k: load_txt(v) for k, v in TOPICS_PATH.items()}


    async def topic_infer(self, question):
        """Infer the user's intention. Identify the topic."""
        rc = self.router.round_chat(
            sys_prom=self.router.config.sys_prompt
        )
        template = QueryAnalysis(question=question)
        prompt = template.format_template()
        res = await rc(prompt, max_tokens=self.router.config.max_token)
        label = template.extract(res)
        return label

    
    async def bryan_answer(self, question:str, bryan_ref:str):
        template = ReferenceTemplate(question=question, bryan_ref=bryan_ref)
        prompt = template.format_template()
        resp = await self.bryan.chat_once(prompt, temperature=self.bryan.config.temperature)
        result = ''
        async for chunk in resp:
            choices = chunk.choices
            if choices:
                chunk = choices[0].delta.content
                if 'Final Answer:' in result:
                    yield chunk
                if chunk:
                    result = f'{result}{chunk}'
        self.full_history.append({'role': 'assistant', 'content': result})
        

    async def tool_answer(self, question:str, history:list):
        tool_names = list(self.bryan.toolkit.keys())
        result = self.tool_caller.tool_call_chat(
            question=question,
            history=history,
            temperature=self.bryan.config.temperature,
            tool_names=tool_names
        )
        async for chunk in result:
            yield chunk
            result = f'{result}{chunk}'
        self.full_history.append({'role': 'assistant', 'content': result})
    

    async def pipe(self, question: str, session_id: str = ''):
        history = MYSQL_STORAGE.query_all(f"select * from {MYSQL_TABLE} where session_id = '{session_id}' order by insert_time asc limit 10")
        history = [{'role': 'user' if item['sender'] == 0 else 'assistant', 'content': item['content']} for item in history]
        self.lite_history = [{'role': 'system', 'content': self.bryan.config.sys_prompt}] + history
        self.full_history = copy.deepcopy(self.lite_history)
        self.lite_history.append({'role': 'user', 'content': question})
        topic_ref = None
        for _ in range(5):
            # Infer topic label
            topic = await self.topic_infer(question)
            # Get topic knowledge
            topic_ref = self.topics.get(topic, None)
            if topic_ref:
                break
        # streaming answer with knowledge base


        if topic == 'General':
            temp_history = copy.deepcopy(self.full_history)
            temp_history[0] = {'role': 'system', 'content': self.tool_caller.config.sys_prompt}
            result = self.tool_answer(question, temp_history)
            async for chunk in result:
                if chunk is not None:
                    yield chunk
        else:
            self.full_history.append({'role': 'user', 'content': question})
            result = self.bryan_answer(question, topic_ref)
            async for chunk in result:
                if chunk is not None:
                    yield chunk
            if 'Final Answer:' not in self.full_history[-1]['content']:
                result = self.tool_answer(question, self.full_history)
                async for chunk in result:
                    if chunk is not None:
                        yield chunk
        self.lite_history.append(copy.deepcopy(self.full_history[-1]))


if __name__ == '__main__':
    import asyncio


    async def main():
        chatbot = BryanChatbot()
        question = 'I want to control my Uric acid.'
        # question = 'Improve the sleep quality'
        # question = 'How is the weather in London now?'
        print(question)
        res = chatbot.pipe(question)
        async for chunk in res:
            if chunk:
                print(chunk, end='')

    asyncio.run(main())