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
