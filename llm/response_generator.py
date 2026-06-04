"""
response_generator.py

Production-grade Natural Language Response Generator
for AI SQL Query Generator systems.

Responsibilities
----------------
- Interpret SQL execution results
- Generate business-friendly insights
- Summarize data outputs
- Ensure conversational UX

Author
------
AI SQL Query Generator Project
"""

import os
import logging
from typing import Dict, Any

import google.generativeai as genai

from dotenv import load_dotenv

from utils.prompt_loader import (
    render_prompt
)


# ---------------------------------------------------------
# ENVIRONMENT CONFIGURATION
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# LOGGER CONFIGURATION
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# GEMINI CONFIGURATION
# ---------------------------------------------------------

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

genai.configure(
    api_key=GEMINI_API_KEY
)


# ---------------------------------------------------------
# MODEL CONFIGURATION
# ---------------------------------------------------------

MODEL_NAME = "gemini-2.5-flash-lite"

TEMPERATURE = 0.3


# ---------------------------------------------------------
# MODEL INITIALIZATION
# ---------------------------------------------------------

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config={
        "temperature": TEMPERATURE
    }
)


# ---------------------------------------------------------
# RESPONSE GENERATION ENGINE
# ---------------------------------------------------------

def generate_natural_language_response(
    user_query: str,
    sql_query: str,
    query_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generates a conversational response based on query results.
    """

    logger.info("Generating natural language response.")

    try:

        # Format results (truncate if too large to prevent token explosion)
        rows = query_result.get("rows", [])
        row_count = query_result.get("row_count", 0)

        # Truncate to top 20 rows for the LLM to analyze
        if len(rows) > 20:
            formatted_result = f"Showing top 20 of {row_count} rows:\n{rows[:20]}"
        else:
            formatted_result = f"Showing all {row_count} rows:\n{rows}"

        # -------------------------------------------------
        # DYNAMIC PROMPT RENDERING
        # -------------------------------------------------

        final_prompt = render_prompt(
            "response_prompt",
            {
                "user_query": user_query,
                "sql_query": sql_query,
                "query_result": formatted_result
            }
        )

        # -------------------------------------------------
        # GEMINI INFERENCE
        # -------------------------------------------------

        response = model.generate_content(final_prompt)
        
        nl_response = response.text.strip()

        logger.info("Natural language response generated successfully.")

        return {
            "success": True,
            "response_text": nl_response
        }

    except Exception as error:

        logger.exception("Failed to generate natural language response.")

        return {
            "success": False,
            "error": str(error),
            "response_text": f"✅ Query executed successfully. Returned {query_result.get('row_count', 0)} rows."
        }
