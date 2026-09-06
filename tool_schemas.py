WEB_SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "name": "web_search",
    "description": "Search the web for current or externally verifiable information.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The web search query.",
            },
            "model": {
                "type": "string",
                "enum": ["gemini-3.5-flash", "gemini-3.5-flash-lite"],
                "default": "gemini-3.5-flash",
                "description": "Gemini model used for the search.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}


GOOGLE_MAPS_TOOL_SCHEMA = {
    "type": "function",
    "name": "google_maps",
    "description": (
        "Search Google Maps for places, businesses, routes, addresses, "
        "and geographic information."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The place, route, address, or geographic query.",
            },
            "model": {
                "type": "string",
                "enum": ["gemini-3.5-flash", "gemini-3.5-flash-lite"],
                "default": "gemini-3.5-flash",
                "description": "Gemini model used for the Maps search.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}


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


TOOL_SCHEMAS = [WEB_SEARCH_TOOL_SCHEMA, GOOGLE_MAPS_TOOL_SCHEMA, BASH_TOOL_SCHEMA]
