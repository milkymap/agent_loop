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
