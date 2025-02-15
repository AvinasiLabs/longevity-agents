import re
import json
from base_agent.prompt_template import BaseTemplate


class DropDuplicationTemplat(BaseTemplate):
    _template = """Identify if the following target news contains the same core event as any of the source news:

[Target news]
{target_news}

[Source news]
{source_news}

Just answer "Yes" or "No", do not add any other words."""

    target_news: str
    source_news: str

    def extract(self, content: str):
        if "yes" in content.lower():
            return "Yes"
        if "no" in content.lower():
            return "No"
        # TODO: Deal with ambiguous answer.
        return "No"
