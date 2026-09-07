from google.genai import Client

from ..base import BaseTool
from .schema import WEB_SEARCH_TOOL_SCHEMA


class WebSearchTool(BaseTool):
    name = "web_search"
    schema = WEB_SEARCH_TOOL_SCHEMA

    def __init__(self, client: Client):
        self.client = client

    async def __call__(self, query: str, model: str = "gemini-3.5-flash") -> str:
        interaction = await self.client.aio.interactions.create(
            model=model,
            system_instruction=(
                "You are a web search engine. Answer the user query using your "
                "Google Search tool."
            ),
            input=[
                {
                    "type": "user_input",
                    "content": [{"type": "text", "text": query}],
                }
            ],
            tools=[{"type": "google_search"}],
        )
        return interaction.output_text
