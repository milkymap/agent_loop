from google.genai import Client

from ..base import BaseTool
from .schema import GOOGLE_MAPS_TOOL_SCHEMA


class GoogleMapsTool(BaseTool):
    name = "google_maps"
    schema = GOOGLE_MAPS_TOOL_SCHEMA

    def __init__(self, client: Client):
        self.client = client

    async def __call__(self, query: str, model: str = "gemini-3.5-flash") -> str:
        interaction = await self.client.aio.interactions.create(
            model=model,
            system_instruction=(
                "You are a Google Maps engine. Answer the user query using your "
                "Google Maps tool."
            ),
            input=[
                {
                    "type": "user_input",
                    "content": [{"type": "text", "text": query}],
                }
            ],
            tools=[{"type": "google_maps"}],
        )
        return interaction.output_text
