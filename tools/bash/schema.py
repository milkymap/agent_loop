BASH_TOOL_SCHEMA = {
    "type": "function",
    "name": "bash",
    "description": "Execute a Bash command and return its exit code, stdout, and stderr.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The Bash command to execute.",
            },
            "working_directory": {
                "type": "string",
                "description": "Optional directory in which to execute the command.",
            },
            "timeout": {
                "type": "integer",
                "minimum": 1,
                "maximum": 300,
                "default": 30,
                "description": "Maximum execution time in seconds.",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    },
}
