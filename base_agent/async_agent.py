#! python3
# -*- encoding: utf-8 -*-
"""
@Time: 2025/02/13 18:01:13
@Author: Louis Jin
@Version: 1.0
@Contact: lululouisjin@gmail.com
@Description: 
"""


import json
import re
import asyncio
from ast import literal_eval
from typing import Callable, Union, List
from openai import OpenAI, AsyncOpenAI, APITimeoutError, APIConnectionError
from pydantic import BaseModel, ConfigDict

# local module
from configs.config_cls import AgentConfig
from utils.logger import logger
from utils.helpers import open_yaml_config
from base_agent.prompt_template import (
    BaseTemplate,
    ReActTemplate,
    SelfAskReActTemplate,
    ToolTemplate,
)


class Message(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="ignore")

    role: str
    content: str


class RichMessage(Message):
    model_config: ConfigDict = ConfigDict(extra="allow")

    name: str
    tools: list = None


class AsyncAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.model = self.config.llm_model
        self.client = AsyncOpenAI(
            api_key=self.config.llm_token, 
            base_url=self.config.llm_uri
        )
        self.messages = [dict(role="system", content=self.config.sys_prompt)]
        self.toolkit = dict()

    def handle_message(
        self, content: str, is_received: bool, callback: Callable = None
    ) -> Message:
        # TODO: add callback function
        message = dict(role="user" if is_received else "assistant", content=content)
        messages = self.messages.copy()
        messages.append(message)
        return messages

    async def chat_once(self, content, temperature=1.0, stop=None):
        messages = self.handle_message(content, is_received=True)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.config.max_token,
            temperature=temperature,
            stop=stop,
        )
        result = response.choices[0].message.content
        return result

    def round_chat(self, sys_prom="You are a helpful assistant.", history:list=None, max_history=30):
        if history is None:
            messages = [{"role": "system", "content": sys_prom}]
        else:
            messages = history[-max_history:]

        def update_messages(content, role):
            messages.append({"role": role, "content": content})

        async def chat(prompt, max_tokens=1024, stop=None, temperature=0.0):
            update_messages(prompt, "user")
            resp = None
            for _ in range(5):
                try:
                    resp = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=max_tokens,
                        stop=stop,
                        temperature=temperature,
                        frequency_penalty=1.5,
                    )
                    if resp.choices[0]:
                        break
                except (APIConnectionError, APITimeoutError) as e:
                    await asyncio.sleep(1)
                    continue
                except Exception as e:
                    raise e

            if resp is None:
                return ""
            content = resp.choices[0].message.content
            update_messages(content, "assistant")
            return content

        return chat

    def stop_truancate(self, stop: Union[List[str], str, None], content):
        # deal with no stop word
        if not stop:
            return content
        if isinstance(stop, str):
            stop = [stop]
        # truncate generated content into content before stop word,
        # as official api may fail sometimes
        for s in stop:
            pattern = rf"[\s\S]+?(?={s})"
            result = re.findall(pattern, content)
            if result:
                return result[0]
        return content

    def construct_tool_doc(
        self, tool_names: List[str] = None, tool_template_cls: BaseTemplate = None
    ):
        tool_doc = ""
        tool_names = list(self.toolkit.keys()) if tool_names is None else tool_names
        tool_template_cls = tool_template_cls or ToolTemplate
        for tool_name in tool_names:
            tool = self.toolkit.get(tool_name, None)
            if tool is None:
                logger.info(f"Tool {tool_name} is not registered for Agent.")
                continue
            tool_template = tool_template_cls(
                tool_name=tool_name,
                description=tool["description"],
                arguments=tool["arguments"],
            )
            tool_des = tool_template.format_template()
            tool_doc += f"{tool_des}\n"
        return tool_doc

    async def tool_call_chat(
        self,
        question: str,
        template_cls: BaseTemplate = None,
        max_round=10,
        temperature=1.0,
        tool_names: List[str] = None,
        content_memory=None,
    ):
        template_cls = template_cls or ReActTemplate
        tool_names = list(self.toolkit.keys()) if tool_names is None else tool_names
        tool_doc = self.construct_tool_doc(tool_names)
        agent_scratchpad = ""
        result = ""
        react_count = 0
        while react_count < max_round:
            template = template_cls(
                tools=tool_doc,
                tool_names=json.dumps(tool_names, ensure_ascii=False),
                question=question,
                agent_scratchpad=agent_scratchpad,
            )
            prompt = template.format_template()
            logger.debug(prompt)
            messages = self.handle_message(prompt, is_received=True)
            for _ in range(5):
                try:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=self.config.max_token,
                        stop=template._stop,
                        temperature=temperature,
                    )
                    if response.choices[0]:
                        break
                except (APIConnectionError, APITimeoutError) as e:
                    await asyncio.sleep(1)
                    continue
                except Exception as e:
                    raise e
            result = response.choices[0].message.content
            # add manual truncation as official api may fail sometimes
            result = self.stop_truancate(template._stop, result)
            logger.debug(result)
            if "Final Answer:" in result:
                break
            obs = ""
            for _ in range(5):
                try:
                    obs = await self.func_call(result, content_memory)
                    break
                except:
                    pass
            agent_scratchpad += f"\n{result}\n{obs}"
            react_count += 1
        return result

    async def selfask_react_chat(self, question, max_round=10, temperature=1.0):
        """Old version tool-call chat.

        Args:
            question (str): the original question asked by human or the third party
            max_round (int, optional): max tool-call round
            temperature (float, optional): the temperature parameter for LLM generation

        Returns:
            str: the content contains final answer or the last generated content if max round meeted
        """
        # add tools
        tool_names = []
        tools = ""
        for tool_name, tool in self.toolkit.items():
            tool_names.append(tool_name)
            tool_template = ToolTemplate(
                tool_name=tool_name,
                description=tool["description"],
                arguments=tool["arguments"],
            )
            tool_des = tool_template.format_template()
            tools += f"{tool_des}\n"
        agent_scratchpad = ""
        result = ""
        react_count = 0
        while react_count < max_round:
            # template = ReActTemplate(
            template = SelfAskReActTemplate(
                tools=tools,
                tool_names=json.dumps(tool_names, ensure_ascii=False),
                question=question,
                agent_scratchpad=agent_scratchpad,
            )
            prompt = template.format_template()
            logger.debug(prompt)
            messages = self.handle_message(prompt, is_received=True)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.config.max_token,
                stop=template._stop,
                temperature=temperature,
            )
            result = response.choices[0].message.content
            # add manual truncation as official api may fail sometimes
            result = self.stop_truancate(template._stop, result)
            logger.debug(result)
            if "Final Answer:" in result:
                break
            obs = await self.func_call(result)
            agent_scratchpad += f"\n{result}\n{obs}"
            react_count += 1
        return result

    async def tool_call_round_chat(
        self,
        question: str,
        tools: str,
        template_cls: BaseTemplate = None,
        max_round=10,
        max_tokens=512,
        temperature=0.2,
        tool_names: List[str] = None,
        sys_prompt=None,
        content_memory=None,
        **kwargs,
    ):
        template_cls = template_cls or ReActTemplate
        max_tokens = max_tokens or self.config.max_token
        sys_prompt = sys_prompt or self.config.sys_prompt
        react_count = 0
        rc = self.round_chat(sys_prompt)
        template = template_cls(question=question, tools=tools, tool_names=tool_names, **kwargs)
        rc_kw = {
            "max_tokens": max_tokens,
            "stop": template._stop,
            "temperature": temperature,
        }
        TOOL_ERROR_MSG = 'Tool calling failed. Please give the final answer directly according to the prompt.'
        prompt = template.format_template()
        logger.debug(prompt)
        result = await rc(prompt, **rc_kw)
        # add manual truncation as official api may fail sometimes
        result = self.stop_truancate(template._stop, result)
        logger.debug(result)
        if "Final Answer:" in result:
            result = template.extract(result)
            return result
        while react_count < max_round:
            obs = ""
            for _ in range(5):
                try:
                    obs = await self.func_call(result, content_memory)
                    if obs:
                        break
                except Exception as e:
                    obs = TOOL_ERROR_MSG
                    pass
            if not obs:
                obs = "No useful information."
            logger.debug(obs)
            result = await rc(obs, **rc_kw)
            logger.debug(result)
            if "Final Answer:" in result or obs == TOOL_ERROR_MSG:
                result = template.extract(result)
                return result
            react_count += 1
        result = await rc(TOOL_ERROR_MSG, **rc_kw)
        result = template.extract(result)
        return result

    def analyze_tool(self, agent_content):
        flag = 0
        action_content = re.findall(
            r"(?<=Action:)[\s\S]+(?=Action Input)", agent_content
        )
        if action_content:
            action_content = action_content[-1]
        else:
            return None, None
        for action in self.toolkit:
            if re.findall(action, action_content, re.I):
                flag += 1
                break
        if flag == 0:
            return None, None
        action_input = re.findall(r"\{[\s\S]+?\}", agent_content, re.I)
        logger.debug(json.loads(action_input[0]))
        return action, literal_eval(action_input[0])

    async def func_call(self, agent_content, content_memory=None):
        action, params = self.analyze_tool(agent_content)
        if not action:
            return ""
        func = self.toolkit[action]["func"]
        if content_memory is not None:
            # get the action memory
            action_memory = content_memory.get(action, dict())
            # get the query handle
            q = params.get("query", None)
            if not q:
                q = params.get("queries", None)
            if q:
                q = json.dumps(q)
                result = action_memory.get(q, None)
                if not result:
                    result = await func(**params)
                    if result:
                        content_memory[action][q] = result
            else:
                result = await func(**params)
        else:
            result = await func(**params)
        obs = f"Observation: {result}"
        logger.debug(obs)
        return obs

    def generate_follow_up(self, agent_content: str, func: Callable):
        follow_up = re.findall("(?<=Follow[ -]up: ).+", agent_content, re.I)
        if not follow_up:
            return ""
        result = func(follow_up[0])
        scratchpad = f"""\nFollow-up: {follow_up[0]}\nIntermediate answer: {result}"""
        return scratchpad

    def clear_history(self):
        self.messages = [self.messages[0]]

    def register_tool(self, name: str, description: str, params: str, func: Callable):
        self.toolkit[name] = {
            "description": description,
            "arguments": params,
            "func": func,
        }

    def register_tool_new(
        self, name: str, description: str, params: dict, required: list, func: Callable
    ):
        self.toolkit[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": params,
                    "required": required,
                },
            },
            "func": func,
        }


if __name__ == "__main__":
    ...
