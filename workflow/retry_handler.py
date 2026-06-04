"""
retry_handler.py

Production-grade SQL retry and recovery engine
for AI SQL Query Generator systems.

Responsibilities
----------------
- Retry failed SQL queries
- Regenerate corrected SQL
- Inject execution errors into prompts
- Track retry attempts
- Validate regenerated SQL
- Improve AI query resilience

This module intentionally avoids:
- direct UI rendering
- schema profiling internals
- database connection management

Author
------
AI SQL Query Generator Project
"""

import os
import re
import logging
from typing import Dict, Any, List

import google.generativeai as genai

from dotenv import load_dotenv

from llm.sql_validator import (
    validate_sql_query
)

from workflow.query_executor import (
    execute_sql_query
)

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

genai.configure(
    api_key=GEMINI_API_KEY
)


# ---------------------------------------------------------
# MODEL CONFIGURATION
# ---------------------------------------------------------

MODEL_NAME = "gemini-2.5-flash-lite"

MAX_RETRY_ATTEMPTS = 3

TEMPERATURE = 0.1


# ---------------------------------------------------------
# GEMINI MODEL
# ---------------------------------------------------------

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config={
        "temperature": TEMPERATURE
    }
)


# ---------------------------------------------------------
# SQL REGENERATION
# ---------------------------------------------------------

def regenerate_sql_query(
    user_query: str,
    failed_sql: str,
    error_message: str
) -> Dict[str, Any]:
    """
    Regenerates corrected SQL query.
    """

    logger.info(
        "Regenerating SQL query."
    )

    try:

        schema_context = (
            generate_schema_context(
                user_query
            )
        )

        retry_prompt = render_prompt(
            "retry_prompt",
            {
                "user_query": user_query,
                "failed_sql": failed_sql,
                "error_message": error_message,
                "schema_context": schema_context
            }
        )

        response = model.generate_content(retry_prompt)

        regenerated_sql = clean_sql_query(
            response.text
        )

        validation_result = (
            validate_sql_query(
                regenerated_sql
            )
        )

        if not validation_result["success"]:

            return {
                "success": False,
                "error":
                    "Regenerated SQL failed validation.",
                "validation_error":
                    validation_result
            }

        return {
            "success": True,
            "corrected_sql":
                regenerated_sql
        }

    except Exception as error:

        logger.exception(
            "SQL regeneration failed."
        )

        return {
            "success": False,
            "error": str(error)
        }


# ---------------------------------------------------------
# MAIN RETRY ENGINE
# ---------------------------------------------------------

def retry_failed_query(
    user_query: str,
    failed_sql: str,
    error_message: str
) -> Dict[str, Any]:
    """
    Main retry orchestration engine.
    """

    logger.info(
        "Starting retry workflow."
    )

    retry_history: List[Dict[str, Any]] = []

    current_sql = failed_sql

    current_error = error_message

    for attempt in range(
        1,
        MAX_RETRY_ATTEMPTS + 1
    ):

        logger.info(
            f"Retry attempt: {attempt}"
        )

        regeneration_result = (
            regenerate_sql_query(
                user_query=user_query,
                failed_sql=current_sql,
                error_message=current_error
            )
        )

        retry_history.append({
            "attempt": attempt,
            "regeneration_result":
                regeneration_result
        })

        if not regeneration_result["success"]:

            current_error = (
                regeneration_result["error"]
            )

            continue

        corrected_sql = (
            regeneration_result[
                "corrected_sql"
            ]
        )

        execution_result = (
            execute_sql_query(
                corrected_sql
            )
        )

        retry_history.append({
            "attempt": attempt,
            "execution_result":
                execution_result
        })

        if execution_result["success"]:

            logger.info(
                "Retry workflow successful."
            )

            return {
                "success": True,
                "retry_attempt":
                    attempt,
                "corrected_sql":
                    corrected_sql,
                "execution_result":
                    execution_result,
                "retry_history":
                    retry_history
            }

        current_sql = corrected_sql

        current_error = execution_result[
            "error"
        ]

    logger.error(
        "All retry attempts exhausted."
    )

    return {
        "success": False,
        "error":
            "Retry attempts exhausted.",
        "retry_history":
            retry_history
    }


# ---------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    failed_query = """
    SELECT revenue_total
    FROM sales_data
    """

    result = retry_failed_query(
        user_query=(
            "Show customer revenue"
        ),
        failed_sql=failed_query,
        error_message=(
            "Invalid column name "
            "'revenue_total'"
        )
    )

    from pprint import pprint

    pprint(result)
