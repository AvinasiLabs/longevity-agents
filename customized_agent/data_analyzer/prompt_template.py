import re
import hjson
import yaml
import zoneinfo
import json5
from ast import literal_eval
from datetime import datetime, timezone
from pydantic import BaseModel

# local module
from base_agent.prompt_template import BaseTemplate


SYS_ROUTER = '''You are an helpful intelligent assistant, think step by step to make tasks done.'''



SYS_ANALYZER = '''**Role:** You are an AI assistant designed to help users understand their *in vitro* (e.g., blood tests, urine tests) or *in vivo* (e.g., imaging reports like MRI, CT scans, endoscopy findings) diagnostic test results.

**Core Task:**
- Receive Input
- Parse & Identify
- Explain the Test
- Interpret Findings
- Structure Output

**CRITICAL SAFETY INSTRUCTIONS & BOUNDARIES:**
- DO NOT PROVIDE A MEDICAL DIAGNOSIS
- DO NOT PROVIDE MEDICAL ADVICE
- DO NOT ACT AS A SUBSTITUTE FOR A HEALTHCARE PROFESSIONAL
- Handle Sensitive Information Appropriately

**Tone:** Be informative, objective, empathetic, and cautious. Avoid sensational or alarming language. Focus on clarifying the provided data.'''


class Classification(BaseTemplate):
    _template = '''Task: Analyze the provided diagnostic results and classify the test indicators according to the given major diagnostic categories.

**Major diagnostic categories**:
{major_cate}

**Diagnostic results**:
{diagno_res}


Instructions:
1. Parse the diagnostic results to extract all test indicators, including their names, results, reference ranges, and any additional information.
2. For each test indicator, determine which of the provided major diagnostic categories it belongs to, based on standard medical classifications. If an indicator fits into multiple categories, choose the most appropriate one.
3. If a test indicator does not fit into any of the provided major categories, group it with other similar unmapped indicators to create new, generalized major categories. Ensure that these new categories are logically named and encompass the indicators appropriately.
4. Organize the output as follows:
   - List each major category (both provided and newly created).
   - Under each major category, list the test indicators that belong to it, along with their results, reference ranges, and explanatory notes, if applicable.
5. Do not output the category that is not available.

Output Format:
- Use a structured JSON format to present the information clearly.

Example:
```JSON
{{
    "provided": [
        {{
            "name": "Blood",
            "information": "Hemoglobin: 14 g/dL (Reference: 12-16 g/dL)\nTotal Leukocyte Count: 5,100 cumm (Reference: 4,800-10,800 cumm)..."
        }},
        {{
            "name": "Hormones",
            "information": "T4: +22%\nEstradiol (Female): +5%\nSex Hormone Binding (Female): -26%..."
        }}
    ],
    "newly_created": [
        {{
            "name": "Lipid",
            "information": "Total cholesterol: 1.3 g/L (Reference: 1.5-2.7 g/L)\nTriglycerides: 1.2 g/L (Reference: 1-1.5 g'L)..."
        }}
    ]
}}
```

Note: The actual categorization should be based on accurate medical knowledge. Ensure that all test indicators are accounted for and that the new categories are appropriately named.'''

    major_cate: str
    diagno_res: str


    def extract(self, content):
        pattern = r"(?<=```JSON)[\s\S]*(?=```)"
        res = re.findall(pattern, content, re.I)
        if res:
            res = res[-1]
            try:
                res = json5.loads(res)
                return res
            except Exception as err:
                raise ValueError(f'Extracting major categories fails:\n{repr(err)}')
        else:
            try:
                res = json5.loads(content)
                return res
            except Exception as err:
                raise ValueError('Empty answer when extracting major categories.')
            

class SubCategory(BaseTemplate):
    _template = '''Task: Analyze the provided diagnostic test results in "{major_cate}" major category and generate structured data along with informative explanations for each sub-item.

Sub-item List: 
{sub_items}

Diagnostic Test Results:
{diagno_res}


Instructions:
1. Parse the diagnostic test results to extract each test indicator, its result, and the reference range.
2. Match each test indicator to the provided sub-item list under the specified major category. If a test indicator does not match any provided sub-item, create a new sub-item with a name and definition inferred from the test indicator and consistent with the major category, add it into newly_created field in the output.
3. For each sub-item (both provided and newly created):
   - Extract the result and reference range.
   - Generate a brief, general-audience explanation of what the sub-item measures and its significance.
   - Check if the result is within the reference range. If outside, indicate whether it is higher or lower.
   - For abnormal results, provide general lifestyle, diet, or exercise suggestions relevant to the sub-item. Clearly state that these are not medical recommendations and that a healthcare professional should be consulted.
4. If any data (e.g., reference range) is missing, note this in the output and proceed with available information.
5. Separate the provided sub-items and newly created sub-items in the output.

Output Format:
Return a JSON object with the following structure:
```JSON
{{
  "provided": [
    {{
      "name": "<sub_item_name_in_title_case>",
      "definition": "<provided_definition>",
      "result": "<result_value>",
      "reference_range": "<reference_range>",
      "explanation": "<significance_explanation>",
      "status": "<within_range | above_range | below_range>",
      "suggestions": "<lifestyle_diet_exercise_suggestions | null>"
    }},
    ...
  ],
  "newly_created": [
    {{
      "name": "<sub_item_name>",
      "definition": "<inferred_definition>",
      "result": "<result_value>",
      "reference_range": "<reference_range>",
      "explanation": "<significance_explanation>",
      "status": "<within_range | above_range | below_range>",
      "suggestions": "<lifestyle_diet_exercise_suggestions | null>"
    }},
    ...
  ]
}}
```

Example:
If the major category is 'Blood', the sub-item list includes 'Hemoglobin', and the test results include 'Hemoglobin' and 'Platelet Count', the output might be:
```JSON
{{
  "provided": [
    {{
      "name": "Hemoglobin",
      "definition": "A protein in red blood cells that carries oxygen",
      "result": "14 g/dL",
      "reference_range": "12-16 g/dL",
      "explanation": "Hemoglobin shows how well your blood carries oxygen. It’s important for energy and overall health.",
      "status": "within_range",
      "suggestions": null
    }}
  ],
  "newly_created": [
    {{
      "name": "Platelet Count",
      "definition": "The number of platelets, which help blood clot",
      "result": "100 x10^9/L",
      "reference_range": "150-400 x10^9/L",
      "explanation": "Platelets help stop bleeding by forming clots. Low levels might make bruising or bleeding more likely.",
      "status": "below_range",
      "suggestions": "Eating nutrient-rich foods like leafy greens and staying hydrated may support overall health. These are general tips, not medical advice. Please consult a healthcare professional."
    }}
  ]
}}
```
Note: Ensure all test indicators are processed, new sub-items are relevant to the major category, and suggestions remain general and non-medical.'''

    major_cate: str
    sub_items: str
    diagno_res: str


    def extract(self, content):
        pattern = r"(?<=```JSON)[\s\S]*(?=```)"
        res = re.findall(pattern, content, re.I)
        if res:
            res = res[-1]
            try:
                res = json5.loads(res)
                return res
            except Exception as err:
                raise ValueError(f'Extracting major categories fails:\n{repr(err)}')
        else:
            try:
                res = json5.loads(content)
                return res
            except Exception as err:
                raise ValueError('Empty answer when extracting major categories.')












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
- Add image's index only if its information is helpful. In the format:
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



