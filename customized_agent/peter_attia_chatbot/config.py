import os

# local module
from configs.config_cls import AgentConfig
from customized_agent.peter_attia_chatbot.prompt_template import (
    SYS_ROUTER,
    SYS_PETER
)


ROUTER_CONFIG = AgentConfig(
  llm_token=os.getenv('AIMLAPI_KEY'),
  llm_uri='https://api.aimlapi.com/v1',
  llm_model='gpt-4o',
  sys_prompt=SYS_ROUTER, 
  max_token=512
)


PETER_CONFIG = AgentConfig(
  llm_token=os.getenv('AIMLAPI_KEY'),
  llm_uri='https://api.aimlapi.com/v1',
  llm_model='gpt-4o-mini',
  sys_prompt=SYS_PETER,
  max_token=8192,
  temperature=0.8
)


TOPICS_PATH = {
    'Exercise': 'customized_agent/peter_attia_chatbot/assets/exercise.txt',
    'Nutrition': 'customized_agent/peter_attia_chatbot/assets/nutrition.txt',
    'Sleep': 'customized_agent/peter_attia_chatbot/assets/sleep.txt',
    'Medications': 'customized_agent/peter_attia_chatbot/assets/medications.txt',
    'Other Tactics': 'customized_agent/peter_attia_chatbot/assets/treatments.txt',
    'Mental': 'customized_agent/peter_attia_chatbot/assets/mental.txt',
    'Risks': 'customized_agent/peter_attia_chatbot/assets/risks.txt',
    'Longevity': 'customized_agent/peter_attia_chatbot/assets/longevity.txt'
}