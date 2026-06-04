"""
sql_validator.py

Production-grade SQL validation engine
for AI SQL Query Generator systems.

Responsibilities
----------------
- Validate generated SQL
- Detect unsafe operations
- Enforce execution policies
- Prevent destructive queries
- Detect malformed SQL

This module intentionally avoids:
- query execution
- AI generation
- schema analysis
- UI rendering

Author
------
AI SQL Query Generator Project
"""

import re
import logging
from typing import Dict, Any


# ---------------------------------------------------------
# LOGGER CONFIGURATION
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# FORBIDDEN SQL OPERATIONS
# ---------------------------------------------------------

FORBIDDEN_KEYWORDS = {
    "DROP",
    "DELETE",
    "TRUNCATE",
    "ALTER",
    "UPDATE",
    "INSERT",
    "MERGE",
    "EXEC",
    "EXECUTE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "DENY",
    "SHUTDOWN",
    "BACKUP",
    "RESTORE"
}


# ---------------------------------------------------------
# DANGEROUS SQL FUNCTIONS
# ---------------------------------------------------------

FORBIDDEN_FUNCTIONS = {
    "xp_cmdshell",
    "sp_execute",
    "sp_executesql",
    "openrowset",
    "opendatasource"
}


# ---------------------------------------------------------
# QUERY NORMALIZATION
# ---------------------------------------------------------

def normalize_sql(
    sql_query: str
) -> str:
    """
    Cleans SQL query safely.
    """

    sql_query = sql_query.strip()

    sql_query = re.sub(
        r"\s+",
        " ",
        sql_query
    )

    return sql_query.strip()


# ---------------------------------------------------------
# MULTI-STATEMENT DETECTION
# ---------------------------------------------------------

def detect_multiple_statements(
    sql_query: str
) -> bool:
    """
    Detects chained SQL statements.
    """

    statements = [
        statement.strip()
        for statement in sql_query.split(";")
        if statement.strip()
    ]

    return len(statements) > 1


# ---------------------------------------------------------
# FORBIDDEN KEYWORD DETECTION
# ---------------------------------------------------------

def detect_forbidden_keywords(
    sql_query: str
) -> list:
    """
    Detects dangerous SQL keywords.
    """

    upper_query = sql_query.upper()

    detected = []

    for keyword in FORBIDDEN_KEYWORDS:

        pattern = rf"\b{keyword}\b"

        if re.search(pattern, upper_query):

            detected.append(keyword)

    return detected


# ---------------------------------------------------------
# FORBIDDEN FUNCTION DETECTION
# ---------------------------------------------------------

def detect_forbidden_functions(
    sql_query: str
) -> list:
    """
    Detects dangerous SQL functions.
    """

    lower_query = sql_query.lower()

    detected = []

    for function in FORBIDDEN_FUNCTIONS:

        pattern = rf"\b{function}\b"

        if re.search(pattern, lower_query):

            detected.append(function)

    return detected


# ---------------------------------------------------------
# SELECT QUERY VALIDATION
# ---------------------------------------------------------

def validate_select_query(
    sql_query: str
) -> bool:
    """
    Ensures query starts with SELECT.
    """

    upper_query = sql_query.upper()

    return upper_query.startswith(
        "SELECT"
    )


# ---------------------------------------------------------
# NESTED QUERY COMPLEXITY
# ---------------------------------------------------------

def detect_query_complexity(
    sql_query: str
) -> Dict[str, Any]:
    """
    Detects potentially expensive queries.
    """

    upper_query = sql_query.upper()

    join_count = upper_query.count(" JOIN ")

    subquery_count = upper_query.count(
        "(SELECT"
    )

    union_count = upper_query.count(
        " UNION "
    )

    return {
        "join_count": join_count,
        "subquery_count":
            subquery_count,
        "union_count": union_count
    }


# ---------------------------------------------------------
# MAIN VALIDATION ENGINE
# ---------------------------------------------------------

def validate_sql_query(
    sql_query: str
) -> Dict[str, Any]:
    """
    Main production-grade SQL validator.
    """

    logger.info(
        "Validating SQL query."
    )

    try:

        normalized_query = normalize_sql(
            sql_query
        )

        # -------------------------------------------------
        # MULTI-STATEMENT CHECK
        # -------------------------------------------------

        if detect_multiple_statements(
            normalized_query
        ):

            return {
                "success": False,
                "error":
                    "Multiple SQL statements detected."
            }

        # -------------------------------------------------
        # SELECT CHECK
        # -------------------------------------------------

        if not validate_select_query(
            normalized_query
        ):

            return {
                "success": False,
                "error":
                    "Only SELECT queries are allowed."
            }

        # -------------------------------------------------
        # FORBIDDEN KEYWORDS
        # -------------------------------------------------

        dangerous_keywords = (
            detect_forbidden_keywords(
                normalized_query
            )
        )

        if dangerous_keywords:

            return {
                "success": False,
                "error":
                    "Forbidden SQL operations detected.",
                "forbidden_keywords":
                    dangerous_keywords
            }

        # -------------------------------------------------
        # FORBIDDEN FUNCTIONS
        # -------------------------------------------------

        dangerous_functions = (
            detect_forbidden_functions(
                normalized_query
            )
        )

        if dangerous_functions:

            return {
                "success": False,
                "error":
                    "Dangerous SQL functions detected.",
                "forbidden_functions":
                    dangerous_functions
            }

        # -------------------------------------------------
        # QUERY COMPLEXITY
        # -------------------------------------------------

        complexity = detect_query_complexity(
            normalized_query
        )

        logger.info(
            "SQL validation successful."
        )

        return {
            "success": True,
            "validated_query":
                normalized_query,
            "complexity": complexity
        }

    except Exception as error:

        logger.exception(
            "SQL validation failed."
        )

        return {
            "success": False,
            "error": str(error)
        }


# ---------------------------------------------------------
# LIGHTWEIGHT VALIDATOR
# ---------------------------------------------------------

def is_query_safe(
    sql_query: str
) -> bool:
    """
    Returns True if query is safe.
    """

    result = validate_sql_query(
        sql_query
    )

    return result["success"]


# ---------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    test_query = """
    SELECT TOP 10 *
    FROM sales_data
    """

    result = validate_sql_query(
        test_query
    )

    from pprint import pprint

    pprint(result)
