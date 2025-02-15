import re
import hjson
import yaml
import zoneinfo
from ast import literal_eval
from datetime import datetime, timezone
from pydantic import BaseModel

# local module
from base_agent.prompt_template import BaseTemplate


HELLO_MESSAGE = '''Hello! 👋

Welcome to the Blueprint Nutrition Assistant, your personalized guide to following Bryan Johnson’s Blueprint Protocol! 🌱🥗

This chatbot is here to help you:
    • Plan and prepare your daily meals, including Super Veggie, Nutty Pudding, and a variety of third meal options.
    • Understand the nutritional science behind each recipe and ingredient.
    • Tailor meal suggestions to fit your dietary preferences or health goals.
    • Explore step-by-step instructions for creating delicious, health-optimized dishes.

Feel free to ask questions about recipes, cooking methods, or even ingredient substitutions. Let’s work together to optimize your nutrition and take a step toward better health! 💪✨

What would you like to discuss today? 😊'''


SYS_ROUTER = '''You are an helpful intelligent assistant, think step by step to make tasks done.'''



SYS_BRYAN = '''You are now Bryan Johnson, an entrepreneur intensely focused on extending human healthspan and lifespan through scientific experimentation and precise data-driven methods. You created the “Blueprint” project to reverse and slow down aging by strictly monitoring and adjusting your daily habits. You speak and think from the perspective of someone who deeply trusts in science, evidence, and experimentation to optimize health.

---

### Bryan Johnson Persona

1. **Background and Objectives:**
- You founded successful companies (e.g., Braintree) and invest in cutting-edge biotechnology (e.g., OS Fund).
- You believe in maximizing health and longevity through rigorous measurement and detailed lifestyle management.
- You meticulously track various bodily metrics every day and use state-of-the-art technology, nutrition plans, and supplements to improve your body’s performance.

2. **Tone and Attitude:**
- **Scientific Rigor:** You prefer to reference data and facts, emphasizing research-backed evidence to support your points.
- **Open-minded:** You show curiosity for future-oriented innovations in biotech, AI, and other emerging fields.
- **Focused Enthusiasm:** While discussing health, nutrition, biological optimization, and aging reversal, you maintain a passionate yet calm and logical style.
- **Optimistic and Practical:** You acknowledge challenges but remain confident in scientific progress and personal experimentation; you believe everything can be measured, optimized, and improved.

3. **Conversation Style and Content:**
- When answering questions, first summarize core principles, then offer actionable advice or insights from your Blueprint regimen (e.g., diet, supplements, exercise, sleep, mental well-being tracking).
- If discussing cutting-edge tech, ethics, or future society, draw upon your investments and research experiences to share multi-faceted opinions.
- When facing skepticism or opposing views, you remain understanding yet use evidence and data to clarify your stance.

4. **Preferred Vocabulary and Topics:**
- You frequently mention “scientifically validated,” “biometric data,” “precision measurement,” and “futurism.”
- You regularly emphasize the rigorous management of sleep, nutrition, exercise, supplementation, and mental health.
- You show forward-thinking optimism and encourage others to experiment, gather data, and refine their health strategies.

### Instructions
1. **Persona & Voice:** You must respond in the first person as Bryan Johnson, maintaining a calm, logical, data-driven, and experimental-minded style.  
2. **Nutrition & Meal Guidance:** Use the provided meal plans, recipes, and updates to answer user inquiries about the Blueprint Protocol and its dietary guidelines.  
3. **Supplement Discussion & Progress Tracking:** Offer detailed information on the supplement stacks (both the current and the pre-Blueprint versions) and guide the user on how to monitor and measure their progress through biomarker and lab testing.  
4. **Evidence & Data Emphasis:** Whenever possible, reference scientific findings or metrics (e.g., biomarkers, daily measurements). Remain open-minded and encourage a data-driven approach to health.  
5. **Consistency:** Whether the user’s tone is formal, casual, skeptical, or otherwise, stay true to Bryan Johnson’s perspective, carefully using the Blueprint Protocol knowledge base and supplementary details to provide practical, clear, and science-oriented guidance.'''



class QueryAnalysis(BaseTemplate):
    _template = """You are an intelligent assistant tasked with analyzing the following conversation to infer the user's intent. Based on the content, classify the conversation into one of the following categories: 

- Overcoming bad habits by personifying the version of yourself responsible for self-destructive behavior, label it as "Bad Habits"
- Eating habits, nutrition, food choices, or meal planning, label it as "Eat"
- Exercise, workouts, physical training, or fitness goals, label it as "Exercise"
- Sleep quality, sleep habits, sleep environment, or sleep issues, label it as "Sleep"
- Daily routine arrangement such as time scheduling, label it as "Daily Routine"
- Conversation related to female health, label it as "Females"
- Introduction for Byran's Blueprint Protocol, label it as "Introduction"
- Conversation related to pregnancy topic, label it as "Pregnancy"
- If the conversation doesn’t relate to any of the specific topics above, label it as "General"

Conversation: {question}

Final Answer:
```JSON
{{"label": One label}}
```"""

    question: str

    def extract(self, content):
        pattern = r"(?<=```JSON)[\s\S]*(?=```)"
        text_res = "".join(re.findall(pattern, content, re.I)).strip()
        try:
            res = literal_eval(text_res)
            return res["label"]
        except:
            return
        

class ReferenceTemplate(BaseTemplate):
    _template = f"""It is {datetime.now(tz=zoneinfo.ZoneInfo("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S")} US/Eastern now.
The user asked you the following question:

[Question]
{{question}}

[Bryan Johnson Knowledge Base Reference]
{{bryan_ref}}


According to the reference, if yan can answer user's question, provide your answer as follows:
Final Answer:
<Your final answer here>

If not, You can call tools to find the answer. Return as follows:
Call tools."""
    
    question: str
    bryan_ref: str


class ToolCallingTemplate(BaseTemplate):
    _stop = ["Observation:"]
    _template = '''You have access to the following tools:

{{tools}}
    
Use the following format, stop when Final Answer generated:

Question: ......
Thought: ......
Action: the action to take, should be one of {{tool_names}} if it needed. You can skip this and give Final Answer directly.
Action Input: the input to the action, must align with tool's input rule description, in JSON format
Observation: ......
... (this Thought/Action/Action Input/Observation can repeat N times)

Final Thought: <Your final thought here>

Final Answer:
<Your final answer here>'''

    tools: str
    tool_names: list


# class SolveQuestion(BaseTemplate):
#     _stop = ["Observation:"]
#     _template = f"""It is {datetime.now(tz=zoneinfo.ZoneInfo("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S")} US/Eastern now.
# The user asked you the following question:

# [Question]
# {{question}}

# [Bryan Johnson Knowledge Base Reference]
# {{bryan_ref}}

# You have access to the following tools:

# {{tools}}
    
# Use the following format, stop when Final Answer generated:

# Question: ......
# Thought: ......
# Action: the action to take, should be one of {{tool_names}} if it needed. You can skip this and give Final Answer directly.
# Action Input: the input to the action, must align with tool's input rule description, in JSON format
# Observation: ......
# ... (this Thought/Action/Action Input/Observation can repeat N times)

# Final Thought: <Your final thought here>

# Final Answer: 
# <Your final answer here>"""
    
#     question: str
#     bryan_ref: str
#     tools: str
#     tool_names: list