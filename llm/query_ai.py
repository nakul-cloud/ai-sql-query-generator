"""
query_ai.py

Production-grade AI SQL generation engine
for schema-aware Text-to-SQL systems.

Responsibilities
----------------
- Build dynamic prompts
- Interact with Gemini LLM
- Generate SQL queries
- Extract valid SQL safely
- Clean malformed outputs
- Support retry workflows

This module intentionally avoids:
- SQL execution
- Streamlit UI
- schema profiling
- orchestration logic

Author
------
AI SQL Query Generator Project
"""

import os
import re
import logging
from typing import Dict, Any

import google.generativeai as genai

from dotenv import load_dotenv

from analysis.schema_context import (
    generate_schema_context
)

from utils.prompt_loader import (
    render_prompt
)

from utils.helpers import (
    clean_sql_query
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

if not GEMINI_API_KEY:

    raise ValueError(
        "GEMINI_API_KEY not found in environment variables."
    )

genai.configure(
    api_key=GEMINI_API_KEY
)


# ---------------------------------------------------------
# MODEL CONFIGURATION
# ---------------------------------------------------------

MODEL_NAME = "gemini-2.5-flash-lite"

TEMPERATURE = 0.1

MAX_OUTPUT_TOKENS = 2048


# ---------------------------------------------------------
# MODEL INITIALIZATION
# ---------------------------------------------------------

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config={
        "temperature": TEMPERATURE,
        "max_output_tokens": MAX_OUTPUT_TOKENS
    }
)




def validate_sql_response(
    sql_query: str
) -> None:
    """
    Basic AI response validation.
    """

    forbidden_keywords = {
        "DROP",
        "DELETE",
        "TRUNCATE",
        "ALTER",
        "UPDATE",
        "INSERT",
        "EXEC"
    }

    upper_query = sql_query.upper()

    for keyword in forbidden_keywords:

        if keyword in upper_query:

            raise ValueError(
                f"Unsafe SQL detected: {keyword}"
            )

    if not upper_query.startswith("SELECT"):

        raise ValueError(
            "Generated SQL is not a SELECT query."
        )


# ---------------------------------------------------------
# MAIN SQL GENERATOR
# ---------------------------------------------------------

def generate_sql_query(
    user_query: str
) -> Dict[str, Any]:
    """
    Main production-grade SQL generator.
    """

    logger.info(
        f"Generating SQL for query: "
        f"{user_query}"
    )

    try:

        # -------------------------------------------------
        # GENERATE SCHEMA CONTEXT
        # -------------------------------------------------

        schema_context = (
            generate_schema_context(
                user_query
            )
        )

        # -------------------------------------------------
        # BUILD PROMPT
        # -------------------------------------------------

        final_prompt = render_prompt(
            "sql_generation",
            {
                "user_query": user_query,
                "schema_context": schema_context
            }
        )

        # -------------------------------------------------
        # GENERATE RESPONSE
        # -------------------------------------------------

        response = model.generate_content(final_prompt)

        raw_output = response.text.strip()

        logger.info(
            "Raw SQL generation successful."
        )

        # -------------------------------------------------
        # CLEAN SQL
        # -------------------------------------------------

        cleaned_sql = clean_sql_query(
            raw_output
        )

        # -------------------------------------------------
        # VALIDATE SQL
        # -------------------------------------------------

        validate_sql_response(
            cleaned_sql
        )

        logger.info(
            "SQL validation successful."
        )

        return {
            "success": True,
            "user_query": user_query,
            "sql_query": cleaned_sql,
            "schema_context": schema_context,
            "raw_response": raw_output
        }

    except Exception as error:

        logger.exception(
            "SQL generation failed."
        )

        return {
            "success": False,
            "user_query": user_query,
            "error": str(error)
        }


# ---------------------------------------------------------
# LIGHTWEIGHT SQL FETCHER
# ---------------------------------------------------------

def get_sql_only(
    user_query: str
) -> str:
    """
    Returns only SQL query string.
    """

    result = generate_sql_query(
        user_query
    )

    if not result["success"]:

        raise RuntimeError(
            result["error"]
        )

    return result["sql_query"]


# ---------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    query = (
        "Show top 10 customers by revenue"
    )

    result = generate_sql_query(
        query
    )

    print("\nGenerated SQL:\n")

    print(result)
