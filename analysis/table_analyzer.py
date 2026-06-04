"""
table_analyzer.py

Production-grade schema-aware table analyzer
for AI SQL Query Generation systems.

Responsibilities
----------------
- Analyze schema relationships
- Rank relevant tables dynamically
- Support scalable query understanding
- Provide context-aware table selection

This module intentionally avoids:
- hardcoded business logic
- dataset-specific assumptions
- static mappings

Future Extensibility
--------------------
Designed for future integration with:
- vector embeddings
- semantic retrieval
- Qdrant
- LangChain
- agentic workflows
"""

import re
import logging
from difflib import SequenceMatcher
from typing import Dict, List, Any

from database.sql_server import get_engine
from database.schema_manager import (
    fetch_database_metadata
)


# ---------------------------------------------------------
# LOGGER CONFIGURATION
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

DEFAULT_SCHEMA = "dbo"

MAX_RETURN_TABLES = 5

MINIMUM_TABLE_SCORE = 0.15


# ---------------------------------------------------------
# QUERY NORMALIZATION
# ---------------------------------------------------------

def normalize_query(
    query: str
) -> List[str]:
    """
    Cleans and tokenizes user query dynamically.
    """

    query = query.lower()

    query = re.sub(
        r"[^a-zA-Z0-9_\s]",
        " ",
        query
    )

    tokens = [
        token.strip()
        for token in query.split()
        if len(token.strip()) > 1
    ]

    return list(set(tokens))


# ---------------------------------------------------------
# STRING SIMILARITY
# ---------------------------------------------------------

def similarity_score(
    value_a: str,
    value_b: str
) -> float:
    """
    Calculates similarity between two strings.
    """

    return SequenceMatcher(
        None,
        value_a.lower(),
        value_b.lower()
    ).ratio()


# ---------------------------------------------------------
# TOKENIZED SCHEMA REPRESENTATION
# ---------------------------------------------------------

def tokenize_schema_name(
    name: str
) -> List[str]:
    """
    Converts schema objects into searchable tokens.

    Example:
    --------
    sales_order_items

    Returns:
    --------
    ["sales", "order", "items"]
    """

    return [
        token.strip()
        for token in name.lower().split("_")
        if token.strip()
    ]


# ---------------------------------------------------------
# COLUMN RELEVANCE
# ---------------------------------------------------------

def calculate_column_relevance(
    query_tokens: List[str],
    column_name: str
) -> float:
    """
    Scores relevance between query and column.
    """

    score = 0.0

    column_tokens = tokenize_schema_name(
        column_name
    )

    for query_token in query_tokens:

        for column_token in column_tokens:

            similarity = similarity_score(
                query_token,
                column_token
            )

            if similarity >= 0.95:
                score += 5.0

            elif similarity >= 0.85:
                score += 3.0

            elif similarity >= 0.70:
                score += 1.5

            elif query_token in column_token:
                score += 1.0

    return score


# ---------------------------------------------------------
# TABLE RELEVANCE
# ---------------------------------------------------------

def calculate_table_relevance(
    query_tokens: List[str],
    table_name: str,
    columns: List[str]
) -> float:
    """
    Calculates dynamic table relevance score.
    """

    score = 0.0

    table_tokens = tokenize_schema_name(
        table_name
    )

    # -----------------------------------------------------
    # TABLE TOKEN MATCHING
    # -----------------------------------------------------

    for query_token in query_tokens:

        for table_token in table_tokens:

            similarity = similarity_score(
                query_token,
                table_token
            )

            if similarity >= 0.95:
                score += 6.0

            elif similarity >= 0.85:
                score += 4.0

            elif similarity >= 0.70:
                score += 2.0

    # -----------------------------------------------------
    # COLUMN CONTEXT MATCHING
    # -----------------------------------------------------

    for column in columns:

        score += calculate_column_relevance(
            query_tokens=query_tokens,
            column_name=column
        )

    # -----------------------------------------------------
    # NORMALIZATION
    # -----------------------------------------------------

    normalization_factor = max(
        len(query_tokens) * len(columns),
        1
    )

    normalized_score = (
        score / normalization_factor
    )

    return round(normalized_score, 4)


# ---------------------------------------------------------
# MAIN TABLE ANALYZER
# ---------------------------------------------------------

def analyze_tables(
    user_query: str,
    max_tables: int = MAX_RETURN_TABLES
) -> List[Dict[str, Any]]:
    """
    Main production-grade table analyzer.
    """

    logger.info(
        f"Analyzing query: {user_query}"
    )

    query_tokens = normalize_query(
        user_query
    )

    metadata = fetch_database_metadata()

    ranked_tables = []

    for table_name, table_data in metadata.items():

        columns = table_data["columns"]

        relevance_score = (
            calculate_table_relevance(
                query_tokens=query_tokens,
                table_name=table_name,
                columns=columns
            )
        )

        if relevance_score < MINIMUM_TABLE_SCORE:
            continue

        matched_columns = []

        for column in columns:

            column_score = (
                calculate_column_relevance(
                    query_tokens,
                    column
                )
            )

            if column_score > 0:
                matched_columns.append({
                    "column_name": column,
                    "score": round(column_score, 4)
                })

        matched_columns = sorted(
            matched_columns,
            key=lambda item: item["score"],
            reverse=True
        )

        ranked_tables.append({
            "table_name": table_name,
            "relevance_score": relevance_score,
            "matched_columns": matched_columns,
            "column_count": len(columns),
            "primary_keys": table_data[
                "primary_keys"
            ]
        })

    ranked_tables = sorted(
        ranked_tables,
        key=lambda item: item[
            "relevance_score"
        ],
        reverse=True
    )

    logger.info(
        f"Relevant tables identified: "
        f"{len(ranked_tables)}"
    )

    return ranked_tables[:max_tables]


# ---------------------------------------------------------
# LIGHTWEIGHT TABLE FETCHER
# ---------------------------------------------------------

def get_relevant_table_names(
    user_query: str
) -> List[str]:
    """
    Returns only table names.
    """

    ranked_tables = analyze_tables(
        user_query
    )

    return [
        table["table_name"]
        for table in ranked_tables
    ]


# ---------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    test_query = (
        "Show monthly revenue by customer"
    )

    output = analyze_tables(
        test_query
    )

    from pprint import pprint

    pprint(output)
