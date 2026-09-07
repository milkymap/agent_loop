
import asyncio

from itertools import chain

from typing import List
from typing_extensions import Self

from google.genai import Client
from google.genai.interactions import Step

from prompt import SYSTEM_PROMPT
from tools import ToolsExecutor

class LLMEngine:
    def __init__(self, client:Client, tools_executor:ToolsExecutor, max_history_turns:int=32):
        self.client = client
        self.tools_executor = tools_executor
        self.max_history_turns = max_history_turns

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, traceback):
        pass

    async def generate_response(self, turns_array:List[List[Step]], turn:List[Step]):
        # sliding window over completed turns: the turn is the natural
        # unit of context eviction
        llmctx = turns_array[-self.max_history_turns:] + [turn]
        llmctx = list(chain(*llmctx))

        output = await self.client.aio.interactions.create(
            model="gemini-3.5-flash",
            input=llmctx,
            system_instruction=SYSTEM_PROMPT,
            tools=self.tools_executor.schemas,
            store=False,
            generation_config={
                "max_output_tokens": 4096,
                "thinking_summaries": "auto"
            }
        )

        return output

    async def loop(self):
        # um, am, tc, tr
        # trajectoire/turn =>[um] + [(tc, tr), (tc, tr), ...., (tc,tr)] + [am]
        # um am
        # um tc,tr, am
        # um tc, tr, tc, tr, tc, tr, ...., am
        # t0, t1, t2, ...., tn => history / context

        turns_array = []
        turn = []
        stop_reason = 0 #
        function_calls = []
        function_results = []
        print("loop...")
        while True:
            try:
                if stop_reason == 0:
                    text = await asyncio.to_thread(input, "user:")
                    if text == "quit":
                        break

                    turn = [
                        {"type": "user_input", "content": [{"type": "text", "text": text}]}
                    ]  # um

                output = await self.generate_response(turns_array, turn)

                function_calls = []
                for step in output.steps:
                    if step.type == "thought":
                        thinking = step.summary[0].text
                        if len(thinking) > 0:
                            print("<thinking>")
                            print(thinking)
                            print("</thinking>")
                            turn.append({
                                "type": "thought",
                                "signature": step.signature,
                                "summary": [{"type": "text", "text": thinking}]
                            })

                    if step.type == "model_output":
                        assistant_message = step.content[0].text
                        print("<answer>")
                        print(assistant_message)
                        print("</answer>")
                        turn.append({
                            "type": "model_output",
                            "content": [{"type": "text", "text": assistant_message}]
                        })

                    if step.type == "function_call":
                        # append in place so the stored turn preserves the
                        # exact step order the model emitted
                        function_call = {
                            "type": "function_call",
                            "name": step.name,
                            "id": step.id,
                            "arguments": step.arguments
                        }
                        turn.append(function_call)
                        function_calls.append(function_call)

                if len(function_calls) > 0:
                    function_results = await self.tools_executor.execute(function_calls)
                    turn.extend(function_results)
                    stop_reason = 1
                    continue

                turns_array.append(turn)

                stop_reason = 0
                function_calls = []
                function_results = []


            except asyncio.CancelledError:
                break


