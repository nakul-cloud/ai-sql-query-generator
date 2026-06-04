"""
query_executor.py

Production-grade SQL execution engine
for AI SQL Query Generator systems.

Responsibilities
----------------
- Execute validated SQL queries
- Handle database execution safely
- Return structured query results
- Protect against oversized responses
- Provide execution metadata

This module intentionally avoids:
- SQL generation
- schema analysis
- UI rendering

Author
------
AI SQL Query Generator Project
"""

import time
import logging
from typing import Dict, Any

import pandas as pd

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database.sql_server import get_engine


# ---------------------------------------------------------
# LOGGER CONFIGURATION
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

MAX_RESULT_ROWS = 1000

QUERY_TIMEOUT_SECONDS = 30


# ---------------------------------------------------------
# SQL LIMIT ENFORCER
# ---------------------------------------------------------

def enforce_row_limit(
    sql_query: str
) -> str:
    """
    Enforces row limiting safely
    for large result prevention.
    """

    upper_query = sql_query.upper()

    if "TOP" in upper_query:
        return sql_query

    if upper_query.startswith("SELECT"):

        return sql_query.replace(
            "SELECT",
            f"SELECT TOP {MAX_RESULT_ROWS}",
            1
        )

    return sql_query


# ---------------------------------------------------------
# RESULT SERIALIZER
# ---------------------------------------------------------

def serialize_dataframe(
    dataframe: pd.DataFrame
) -> Dict[str, Any]:
    """
    Converts dataframe into structured response.
    """

    return {
        "columns": dataframe.columns.tolist(),
        "rows": dataframe.to_dict(
            orient="records"
        ),
        "row_count": len(dataframe)
    }


# ---------------------------------------------------------
# MAIN QUERY EXECUTOR
# ---------------------------------------------------------

def execute_sql_query(
    sql_query: str
) -> Dict[str, Any]:
    """
    Executes SQL query safely.
    """

    logger.info(
        "Executing SQL query."
    )

    start_time = time.time()

    try:

        # -------------------------------------------------
        # ENFORCE SAFE ROW LIMIT
        # -------------------------------------------------

        safe_query = enforce_row_limit(
            sql_query
        )

        logger.info(
            f"Final SQL Query: {safe_query}"
        )

        engine = get_engine()

        # -------------------------------------------------
        # EXECUTE QUERY
        # -------------------------------------------------

        with engine.connect() as connection:

            connection.execute(
                text(
                    f"SET LOCK_TIMEOUT "
                    f"{QUERY_TIMEOUT_SECONDS * 1000}"
                )
            )

            dataframe = pd.read_sql(
                text(safe_query),
                connection
            )

        execution_time = round(
            time.time() - start_time,
            3
        )

        logger.info(
            f"Query executed successfully "
            f"in {execution_time}s"
        )

        # -------------------------------------------------
        # SERIALIZE RESULTS
        # -------------------------------------------------

        serialized_results = (
            serialize_dataframe(
                dataframe
            )
        )

        return {
            "success": True,
            "sql_query": safe_query,
            "execution_time_seconds":
                execution_time,
            "result": serialized_results
        }

    except SQLAlchemyError as error:

        logger.exception(
            "Database execution failed."
        )

        return {
            "success": False,
            "sql_query": sql_query,
            "error_type": "DATABASE_ERROR",
            "error": str(error)
        }

    except Exception as error:

        logger.exception(
            "Unexpected execution error."
        )

        return {
            "success": False,
            "sql_query": sql_query,
            "error_type": "SYSTEM_ERROR",
            "error": str(error)
        }


# ---------------------------------------------------------
# LIGHTWEIGHT DATAFRAME EXECUTOR
# ---------------------------------------------------------

def execute_query_as_dataframe(
    sql_query: str
) -> pd.DataFrame:
    """
    Returns dataframe only.
    """

    engine = get_engine()

    safe_query = enforce_row_limit(
        sql_query
    )

    with engine.connect() as connection:

        dataframe = pd.read_sql(
            text(safe_query),
            connection
        )

    return dataframe


# ---------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    test_query = """
    SELECT *
    FROM sales_data
    """

    result = execute_sql_query(
        test_query
    )

    from pprint import pprint

    pprint(result)
