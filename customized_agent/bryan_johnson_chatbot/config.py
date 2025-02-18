import os

# local module
from configs.config_cls import AgentConfig
from customized_agent.bryan_johnson_chatbot.prompt_template import (
    SYS_ROUTER,
    SYS_BRYAN
)


ROUTER_CONFIG = AgentConfig(
  llm_token=os.getenv('AIMLAPI_KEY'),
  llm_uri='https://api.aimlapi.com/v1',
  llm_model='gpt-4o',
  sys_prompt=SYS_ROUTER, 
  max_token=512
)


BRYAN_CONFIG = AgentConfig(
  llm_token=os.getenv('AIMLAPI_KEY'),
  llm_uri='https://api.aimlapi.com/v1',
  llm_model='gpt-4o-mini',
  sys_prompt=SYS_BRYAN,
  max_token=8192,
  temperature=0.8
)


TOPICS_PATH = {
    'Bad Habits': 'customized_agent/bryan_johnson_chatbot/assets/bad_habits.txt',
    'Eat': 'customized_agent/bryan_johnson_chatbot/assets/eat.txt',
    'Exercise': 'customized_agent/bryan_johnson_chatbot/assets/exercise.txt',
    'Sleep': 'customized_agent/bryan_johnson_chatbot/assets/sleep.txt',
    'Daily Routine': 'customized_agent/bryan_johnson_chatbot/assets/daily_routine.txt',
    'Females': 'customized_agent/bryan_johnson_chatbot/assets/females.txt',
    'Introduction': 'customized_agent/bryan_johnson_chatbot/assets/introduction.txt',
    'Pregnancy': 'customized_agent/bryan_johnson_chatbot/assets/pregnancy.txt',
    'General': 'customized_agent/bryan_johnson_chatbot/assets/protocol.txt'
}