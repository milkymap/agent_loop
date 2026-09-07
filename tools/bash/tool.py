import asyncio
import json

from ..base import BaseTool
from .schema import BASH_TOOL_SCHEMA


class BashTool(BaseTool):
    name = "bash"
    schema = BASH_TOOL_SCHEMA

    async def __call__(
        self,
        command: str,
        working_directory: str | None = None,
        timeout: int = 30,
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
