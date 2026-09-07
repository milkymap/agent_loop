import asyncio
import json

from typing import Any, Dict, List

from .base import BaseTool


class ToolsExecutor:
    """Holds the tool registry and turns function calls into function results.

    The tool namespace is exactly the tools handed to the constructor. A
    failure is an observation, not a crash: unknown names and raised
    exceptions come back as error-bearing results in the trajectory.
    """

    def __init__(self, tools: List[BaseTool]):
        self.tools = {tool.name: tool for tool in tools}

    @property
    def schemas(self) -> List[Dict[str, Any]]:
        return [tool.schema for tool in self.tools.values()]

    async def run_function(self, name: str, id: str, arguments: Dict) -> Dict:
        print(name)
        print(json.dumps(arguments, indent=3))

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

    async def execute(self, function_calls: List[Dict]) -> List[Dict]:
        tasks = [
            self.run_function(fc["name"], fc["id"], fc["arguments"])
            for fc in function_calls
        ]
        return await asyncio.gather(*tasks)
