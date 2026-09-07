import asyncio

from dotenv import load_dotenv
from google.genai import Client

from settings import LLMSettings
from engine import LLMEngine
from tools import ToolsExecutor, WebSearchTool, GoogleMapsTool, BashTool

def main():
    print("Hello from gemini-llm!")
    llm_settings = LLMSettings()
    print(llm_settings)

    async def main_loop():
        print("inner async loop")
        client = Client(api_key=llm_settings.gemini_api_key.get_secret_value())
        tools_executor = ToolsExecutor(tools=[
            WebSearchTool(client=client),
            GoogleMapsTool(client=client),
            BashTool(),
        ])
        async with LLMEngine(client=client, tools_executor=tools_executor) as llm:
            await llm.loop()

    asyncio.run(main=main_loop())

if __name__ == "__main__":
    load_dotenv()
    main()
