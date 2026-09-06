import asyncio 

from itertools import chain 
from dotenv import load_dotenv

from settings import LLMSettings
from engine import LLMEngine

def main():
    print("Hello from gemini-llm!")
    llm_settings = LLMSettings()
    print(llm_settings)

    async def main_loop():
        print("inner async loop")
        async with LLMEngine(gemini_api_key=llm_settings.gemini_api_key.get_secret_value()) as llm:
            await llm.loop()

    asyncio.run(main=main_loop())

if __name__ == "__main__":
    load_dotenv()
    main()
