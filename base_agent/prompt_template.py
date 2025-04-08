from pydantic import BaseModel, ConfigDict, Field
from typing import Union, List


class BaseTemplate(BaseModel):
    model_config: ConfigDict = ConfigDict(extra="allow")
    _template: str
    _stop: Union[str, List[str], None] = None

    def format_template(self):
        return self._template.format(**self.model_dump())

    def safe_word(self):
        return self._stop

    def extract(self, content):
        return content


class ReActTemplate(BaseTemplate):
    tools: str
    tool_names: str
    question: str
    agent_scratchpad: str

    _stop = ["Observation:"]
    _template = """Answer the following question as best you can, think step by step. 
    
Question: {question}
    
You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of {tool_names} if it needed. You can skip this and give Final Answer directly.
Action Input: the input to the action, must align with tool's input rule description, kwargs in JSON format:
```JSON
{{
    key: value
}}
```
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

{agent_scratchpad}"""


class ReActTemplateDot(BaseTemplate):
    tools: str
    tool_names: str
    question: str
    agent_scratchpad: str

    _stop = ["Observation:"]
    _template = """Answer the following questions as best you can, think step by step. You have access to the following tools:

{tools}

Use the following format, stop when Final Answer generated:

Question: ......
Thought: ......
Action: the action to take, should be one of {tool_names} if it needed. You can skip this and give Final Answer directly.
Action Input: the input to the action, must align with tool's input rule description, in JSON format
Observation: ......
... (this Thought/Action/Action Input/Observation can repeat N times)
Final Thought: ......
Final Answer: ......

Begin!

Question: {question}
{agent_scratchpad}"""


class MultiReActTemplate(BaseTemplate):
    tools: str
    tool_names: str
    question: str
    agent_scratchpad: str

    _stop = ["Observation:"]
    _template = """Answer the following questions as best you can, think step by step. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of {tool_names} if it needed
Action Input: the input to the action, must align with tool's input rule description, in JSON format
Observation: the result of the action
Thought: optimal new round of thought if needed
Action: ...
Action Input: ...
Observation: ...
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {question}
{agent_scratchpad}"""


class ReActTemplateZH(BaseTemplate):
    tools: str
    tool_names: str
    question: str
    agent_scratchpad: str

    _stop = ["Observation:"]
    _template = """一步接一步进行思考，尽你所能回答以下问题，你可以使用以下工具:

{tools}

使用以下格式:

Question: 你需要回答的问题
Key Concept: 识别到的最为关键的概念
Thought: 对回答回题所进行的思考
Action: 需要采取的行动（如果有必要）, 应当是以下工具中的一个 {tool_names} 
Action Input: 行动的输入值, 必须严格遵守工具描述中的规范, 使用 JSON 格式，不要和之前的输入重复
Observation: 行动的输出结果
Thought: 以上输出是否足以回答问题，是否需进行新一轮的行动（如果有必要）
... (Thought/Action/Action Input/Observation 可以重复多轮)
Thought: 对最终回答的思考
Final Answer: 对于原问题的最终回答

开始吧！

Question: {question}
{agent_scratchpad}"""


# class MultiReActTemplateZH(BaseTemplate):
#     tools: str
#     tool_names: str
#     question: str
#     agent_scratchpad: str

#     _stop = 'Observation:'
#     _template = """Answer the following questions as best you can, think step by step. You have access to the following tools:

# {tools}

# Use the following format:

# Question: the input question you must answer
# Thought: you should always think about what to do
# Action: the action to take, should be one of {tool_names} if it needed
# Action Input: the input to the action, must align with tool's input rule description, in JSON format
# Observation: the result of the action
# Thought: optimal new round of thought if needed
# Action: ...
# Action Input: ...
# Observation: ...
# ... (this Thought/Action/Action Input/Observation can repeat N times)
# Thought: I now know the final answer
# Final Answer: the final answer to the original input question

# Begin!

# Question: {question}
# {agent_scratchpad}"""


class SelfAskTemplate(BaseTemplate):
    question: str
    agent_scratchpad: str

    _stop = "Intermediate answer:"
    _template = """Question: Who lived longer, Muhammad Ali or Alan Turing?
Are follow-up questions needed here: Yes.
Follow-up: How old was Muhammad Ali when he died?
Intermediate answer: Muhammad Ali was 74 years old when he died.
Follow-up: How old was Alan Turing when he died?
Intermediate answer: Alan Turing was 41 years old when he died.
... (this Follow up questions/Follow up/Intermediate answer can repeat N times)
Final Answer: Muhammad Ali

Question: {question}
Are followup questions needed here:{agent_scratchpad}"""


class SelfAskReActTemplate(BaseTemplate):
    tools: str
    tool_names: str
    question: str
    agent_scratchpad: str

    _stop = ["OBS:", "Observation:"]
    _template = """Answer the following question as best you can, think step by step. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do, decide if a follow-up questions needed here.
Follow-up: the follow-up questions if needed
Action: the action to take, should be one of {tool_names} if it needed
Action Input: the input to the action, must align with tool's input rule description, in JSON format
Observation: the result of the action
Intermediate answer: the intermediate answer if needed
... (this Thought/Follow-up/Action/Action Input/Observation/Intermediate answer can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {question}
{agent_scratchpad}"""


class ToolTemplate(BaseTemplate):
    tool_name: str
    description: str
    arguments: str

    _template = """{tool_name}
    description: {description}
    arguments: {arguments}"""


# class Parameters(BaseModel):
#     type: str = Field('object')
#     properties: dict
#     required: list


# class Function(BaseModel):
#     name: str
#     description: str
#     parameters: Parameters


# class Tool(BaseModel):
#     type: str = Field('function')
#     function: Function


if __name__ == "__main__":
    react = ReActTemplate(tools="a", tool_names="b", question="c", agent_scratchpad="")
    ...
