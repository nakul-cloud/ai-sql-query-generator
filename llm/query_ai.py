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
# SYSTEM PROMPT
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are an expert Microsoft SQL Server engineer.

Your task is to generate accurate,
optimized, production-grade SQL queries.

STRICT RULES:
--------------
1. Generate ONLY valid Microsoft SQL Server syntax.
2. Never hallucinate table names.
3. Never hallucinate column names.
4. Use ONLY provided schema context.
5. Never generate destructive queries.
6. Only generate SELECT queries.
7. Never use markdown formatting.
8. Never explain the SQL.
9. Never wrap SQL in triple backticks.
10. Return ONLY executable SQL.

QUERY REQUIREMENTS:
-------------------
- Use proper aliases
- Use aggregation correctly
- Use TOP instead of LIMIT
- Handle grouping safely
- Prefer readable formatting
- Avoid SELECT *

Your response must contain ONLY SQL.
"""


# ---------------------------------------------------------
# GEMINI MODEL INITIALIZATION
# ---------------------------------------------------------

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config={
        "temperature": TEMPERATURE,
        "max_output_tokens": MAX_OUTPUT_TOKENS
    }
)


# ---------------------------------------------------------
# PROMPT BUILDER
# ---------------------------------------------------------

def build_sql_prompt(
    user_query: str,
    schema_context: str
) -> str:
    """
    Builds dynamic schema-aware prompt.
    """

    prompt = f"""
Database Schema Context:
------------------------
{schema_context}

User Question:
--------------
{user_query}

Generate a valid Microsoft SQL Server query.
"""

    return prompt.strip()


# ---------------------------------------------------------
# SQL EXTRACTION
# ---------------------------------------------------------

def extract_sql_query(
    response_text: str
) -> str:
    """
    Cleans and extracts executable SQL.
    """

    cleaned = response_text.strip()

    # Remove markdown code blocks
    cleaned = re.sub(
        r"```sql",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    cleaned = re.sub(
        r"```",
        "",
        cleaned
    )

    # Remove accidental explanations
    cleaned = cleaned.strip()

    return cleaned


# ---------------------------------------------------------
# SQL SAFETY VALIDATION
# ---------------------------------------------------------

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

        final_prompt = build_sql_prompt(
            user_query=user_query,
            schema_context=schema_context
        )

        # -------------------------------------------------
        # GENERATE RESPONSE
        # -------------------------------------------------

        response = model.generate_content(
            [
                SYSTEM_PROMPT,
                final_prompt
            ]
        )

        raw_output = response.text.strip()

        logger.info(
            "Raw SQL generation successful."
        )

        # -------------------------------------------------
        # CLEAN SQL
        # -------------------------------------------------

        cleaned_sql = extract_sql_query(
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
