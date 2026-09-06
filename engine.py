
import asyncio 
import json 

from itertools import chain

from typing import List, Tuple, Dict, Any, Optional 
from typing_extensions import Self 

from google.genai import Client 
from google.genai.interactions import Step, FunctionCallStep, FunctionResultStep

from prompt import SYSTEM_PROMPT
from tool_schemas import TOOL_SCHEMAS

class LLMEngine:
    def __init__(self, gemini_api_key:str):
        self.gemini_api_key = gemini_api_key

    async def __aenter__(self) -> Self:
        self.client = Client(api_key=self.gemini_api_key)
        # explicit registry: the tool namespace is exactly these entries,
        # not every method of the object
        self.tools = {
            "web_search": self.web_search,
            "google_maps": self.google_maps,
            "bash": self.bash,
        }
        return self

    async def __aexit__(self, exc_type, exc_val, traceback):
        pass 

    async def generate_response(self, turns_array:List[List[Step]], turn:List[Step]):
        llmctx = turns_array + [turn]
        llmctx = list(chain(*llmctx))

        output = await self.client.aio.interactions.create(
            model="gemini-3.5-flash",
            input=llmctx,
            system_instruction=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            store=False,
            generation_config={
                "max_output_tokens": 4096,
                "thinking_summaries": "auto"
            }
        )

        return output

    async def web_search(self, query:str, model:str="gemini-3.5-flash") -> str:
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

    async def google_maps(self, query:str, model:str="gemini-3.5-flash") -> str:
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

    async def bash(
        self,
        command:str,
        working_directory:str | None=None,
        timeout:int=30,
    ) -> str:

        process = await asyncio.create_subprocess_exec(
            "bash",
            "-c",
            command,
            cwd=working_directory,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except TimeoutError:
            process.kill()
            await process.communicate()
            return json.dumps({
                "command": command,
                "error": f"Command timed out after {timeout} seconds",
            })

        return json.dumps({
            "command": command,
            "exit_code": process.returncode,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        })

    async def execute_tools(self, function_calls:List) -> List:
        async def run_function(name:str, id:str, arguments:Dict):
            print(name)
            print(json.dumps(arguments, indent=3))

            # a failure is an observation, not a crash: it goes back into
            # the trajectory so the model can self-correct
            try:
                tool = self.tools[name]
            except KeyError:
                data = json.dumps({"error": f"unknown tool: {name}"})
            else:
                try:
                    data = await tool(**arguments)
                except Exception as error:
                    data = json.dumps({
                        "error": f"{type(error).__name__}: {error}",
                    })

            return {
                "type": "function_result", 
                "call_id": id, 
                "name": name, 
                "result": [{"type": "text", "text": data}]
            }

        tasks = [ run_function(fc["name"], fc["id"], fc["arguments"]) for fc in function_calls]
        function_results = await asyncio.gather(*tasks)
        return function_results


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
                        function_calls.append(
                            {
                                "type": "function_call", 
                                "name": step.name, 
                                "id": step.id, 
                                "arguments": step.arguments
                            }
                        )

                if len(function_calls) > 0: 
                    function_results = await self.execute_tools(function_calls)
                    turn.extend(function_calls)
                    turn.extend(function_results)
                    stop_reason = 1
                    continue

                turns_array.append(turn)

                stop_reason = 0
                function_calls = []
                function_results = []
                        

            except asyncio.CancelledError:
                break  

    
