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

I’m Longevity AI, your personal assistant for exploring the latest medical research on longevity and health. Whether you have questions about aging, life extension strategies, or insights from cutting-edge scientific papers, I’m here to help!

Ask me anything about longevity, and I’ll provide answers based on peer-reviewed research. Let’s unlock the secrets to a longer, healthier life together!

Disclaimer: The information I provide is based on scientific studies and should not be considered as medical advice. Always consult with a healthcare professional before making any decisions related to your health and well-being.'''


SYS_ROUTER = '''You are an helpful intelligent assistant, think step by step to make tasks done.'''



SYS_PAPER = '''You are a specialized AI expert in longevity research and scientific paper analysis. Your purpose is to assist in generating comprehensive, evidence-based answers to queries about aging, longevity interventions, and related biomedical research by synthesizing information from retrieved paper chunks. When provided with text segments from research papers, you must:

- Thoroughly analyze and interpret the content, identifying key findings, methodologies, limitations, and implications relevant to longevity research.
- Synthesize insights across multiple sources, compare and contrast study results, and integrate disparate pieces of evidence into a coherent, well-structured answer.
- Present your analysis in a clear, organized format (using sections like “Background”, “Methods”, “Key Findings”, “Implications”, etc., if needed).
- Maintain a neutral, objective tone, explicitly noting any uncertainties or gaps in the research, and suggesting avenues for further investigation if relevant.
- Base your responses strictly on the evidence provided by the retrieved paper chunks, ensuring that your generated answers are accurate, relevant, and fully supported by the available data.
- Adapt your depth and technical detail according to the complexity of the query while remaining concise and clear.

Your analysis should empower users with a deep, nuanced understanding of longevity research by integrating the latest scholarly evidence into actionable insights.'''



class QueryAnalysis(BaseTemplate):
    _template = """According to the user submitted question, determine whether the query requires specialized, evidence-based insights from the longevity paper knowledge base or if it can be answered directly using general knowledge. 


## Question:
{question}    


## Instructions:
Analyze the user's question for technical specificity:
- If the query involves detailed experimental methodologies, specific study results, advanced terminology, or references to recent research findings in longevity, mark it as “RETRIEVAL NEEDED”.
- If the question is broad, conceptual, or based on common knowledge unrelated to aging or longevity, mark it as “GENERAL ANSWER”.


Return in the format:
“RETRIEVAL NEEDED” or “GENERAL ANSWER”"""

    question: str

    def extract(self, content: str):
        pattern = "retriev"
        if pattern in content.lower():
            return "RETRIEVAL"
        else:
            return "GENERAL"
        

class ReferenceTemplate(BaseTemplate):
    _template = f"""It is {datetime.now(tz=zoneinfo.ZoneInfo("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S")} US/Eastern now.

The user asked you the following question:

## Question:
{{question}}


You have obtained the following longevity paper snippets as reference:

## Reference:
{{ref}}


## Instructions:
- Keep answer concise and precise.
- Must answer with image's index if its information is helpful. In the format:
    Reference Image:
    <image>index</image>
- Do not output content dosen't belong to the answer.

According to the reference, if yan can answer user's question, provide your answer as follows:
Final Answer:
<Your final answer here>

If not, You can use web search tool to find the answer. Return as follows:
Call tools."""
    
    question: str
    ref: str



