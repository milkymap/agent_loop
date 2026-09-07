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


MEMORY_TOOL_SCHEMA = {
    "type": "function",
    "name": "memory",
    "description": (
        "Persistent memory across conversations, stored as virtual files under "
        "/memories. Check your memory at the start of a task (view /memories or "
        "search), and record important facts, progress, and user preferences as "
        "you work. `search` retrieves entries by semantic similarity, not exact "
        "match. Keep the memory organized: update or delete stale entries."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": [
                    "view", "create", "str_replace", "insert",
                    "delete", "rename", "search",
                ],
                "description": "The memory operation to perform.",
            },
            "path": {
                "type": "string",
                "description": (
                    "Path of the memory entry, starting with /memories "
                    "(e.g. /memories/user_preferences.md). Use /memories "
                    "with `view` to list all entries."
                ),
            },
            "file_text": {
                "type": "string",
                "description": "Content to write (for `create`).",
            },
            "old_str": {
                "type": "string",
                "description": "Exact text to replace (for `str_replace`).",
            },
            "new_str": {
                "type": "string",
                "description": (
                    "Replacement text (for `str_replace`); omit to delete "
                    "old_str."
                ),
            },
            "insert_line": {
                "type": "integer",
                "description": "Line after which to insert (for `insert`); 0 inserts at the top.",
            },
            "insert_text": {
                "type": "string",
                "description": "Text to insert (for `insert`).",
            },
            "view_range": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "[start_line, end_line] for `view`; -1 as end means end of file.",
            },
            "old_path": {
                "type": "string",
                "description": "Current path (for `rename`).",
            },
            "new_path": {
                "type": "string",
                "description": "New path (for `rename`).",
            },
            "query": {
                "type": "string",
                "description": "Natural-language query (for `search`).",
            },
            "top_k": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "default": 5,
                "description": "Number of results to return (for `search`).",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    },
}


TOOL_SCHEMAS = [
    WEB_SEARCH_TOOL_SCHEMA,
    GOOGLE_MAPS_TOOL_SCHEMA,
    BASH_TOOL_SCHEMA,
    MEMORY_TOOL_SCHEMA,
]
