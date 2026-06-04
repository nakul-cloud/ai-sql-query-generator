"""
constants.py

Centralized constants and configuration
for AI SQL Query Generator systems.

Responsibilities
----------------
- Centralize magic strings
- Store default configuration values
- Manage intent mappings

Author
------
AI SQL Query Generator Project
"""

# Gemini Defaults
DEFAULT_MODEL_NAME = "gemini-2.5-flash-lite"
DEFAULT_TEMPERATURE = 0.0

# Intents
INTENT_DATA_QUERY = "DATA_QUERY"
INTENT_GENERAL_CHAT = "GENERAL_CHAT"
INTENT_UNSAFE_REQUEST = "UNSAFE_REQUEST"
INTENT_UNKNOWN = "UNKNOWN"

# App Defaults
DEFAULT_APP_TITLE = "AI SQL Query Generator"
