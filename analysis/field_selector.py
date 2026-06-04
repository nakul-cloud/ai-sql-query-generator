# analysis/field_selector.py
"""
field_selector.py

Purpose
-------
Dynamically selects the most relevant database fields
for a user's natural language query.

This module is designed for production-grade
schema-aware AI SQL systems.

Responsibilities
----------------
- Dynamically analyze schema metadata
- Rank relevant columns
- Infer semantic relevance
- Detect relationship strength
- Support scalable multi-table querying

This module DOES NOT
--------------------
- Generate SQL
- Execute SQL
- Call Streamlit
- Handle prompt engineering

Architecture Notes
------------------
This implementation avoids:
- hardcoded business keywords
- fixed field mappings
- dataset-specific assumptions

Instead, it uses:
- schema metadata
- SQL datatypes
- similarity scoring
- contextual relevance
- dynamic ranking

Author
------
AI SQL Query Generator Project
"""

import re
import logging
from difflib import SequenceMatcher
from typing import Dict, List, Any

from analysis.table_analyzer import (
    analyze_tables
)

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

MIN_FIELD_SCORE = 0.15

MAX_FIELDS_PER_TABLE = 15


# ---------------------------------------------------------
# QUERY NORMALIZATION
# ---------------------------------------------------------

def normalize_query(
    query: str
) -> List[str]:
    """
    Cleans and tokenizes user query.

    Example:
    --------
    "Show monthly sales revenue"

    Returns:
    --------
    ["show", "monthly", "sales", "revenue"]
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
        if token.strip()
    ]

    return tokens


# ---------------------------------------------------------
# STRING SIMILARITY
# ---------------------------------------------------------

def similarity_score(
    source: str,
    target: str
) -> float:
    """
    Calculates similarity score between strings.

    Returns:
    --------
    Float between 0 and 1
    """

    return SequenceMatcher(
        None,
        source.lower(),
        target.lower()
    ).ratio()


# ---------------------------------------------------------
# COLUMN TOKENIZATION
# ---------------------------------------------------------

def tokenize_column_name(
    column_name: str
) -> List[str]:
    """
    Breaks column names into semantic tokens.

    Example:
    --------
    customer_revenue_amount

    Returns:
    --------
    ["customer", "revenue", "amount"]
    """

    return [
        token.strip()
        for token in column_name.lower().split("_")
        if token.strip()
    ]


# ---------------------------------------------------------
# DATATYPE WEIGHTING
# ---------------------------------------------------------

def datatype_weight(
    sql_datatype: str
) -> float:
    """
    Dynamically weights fields
    based on SQL datatype.

    Purpose:
    --------
    Numerical/date columns are often
    more important in analytics queries.
    """

    datatype = sql_datatype.lower()

    numeric_types = {
        "int",
        "bigint",
        "smallint",
        "tinyint",
        "float",
        "real",
        "decimal",
        "numeric",
        "money"
    }

    date_types = {
        "date",
        "datetime",
        "datetime2",
        "timestamp",
        "smalldatetime"
    }

    text_types = {
        "varchar",
        "nvarchar",
        "text",
        "char"
    }

    if datatype in numeric_types:
        return 1.25

    if datatype in date_types:
        return 1.15

    if datatype in text_types:
        return 1.0

    return 0.90


# ---------------------------------------------------------
# COLUMN RELEVANCE SCORING
# ---------------------------------------------------------

def calculate_field_score(
    query_tokens: List[str],
    column_name: str,
    column_type: str
) -> float:
    """
    Calculates contextual field relevance.

    Scoring Factors:
    ----------------
    - exact token matches
    - partial matches
    - semantic similarity
    - datatype weighting
    """

    score = 0.0

    column_tokens = tokenize_column_name(
        column_name
    )

    for query_token in query_tokens:

        for column_token in column_tokens:

            similarity = similarity_score(
                query_token,
                column_token
            )

            # Exact/near exact match
            if similarity >= 0.95:
                score += 4.0

            # Strong semantic match
            elif similarity >= 0.80:
                score += 2.5

            # Moderate semantic match
            elif similarity >= 0.65:
                score += 1.5

            # Partial substring match
            elif query_token in column_token:
                score += 1.0

    # Datatype influence
    score *= datatype_weight(column_type)

    return round(score, 4)


# ---------------------------------------------------------
# COLUMN RELATIONSHIP DETECTION
# ---------------------------------------------------------

def detect_related_columns(
    columns: List[str]
) -> Dict[str, List[str]]:
    """
    Detects potential relationships
    between columns.

    Example:
    --------
    customer_id
    customer_name

    grouped together semantically.
    """

    relationships = {}

    for column in columns:

        root_token = column.split("_")[0]

        related = []

        for candidate in columns:

            if candidate == column:
                continue

            if candidate.startswith(root_token):
                related.append(candidate)

        relationships[column] = related

    return relationships


# ---------------------------------------------------------
# MAIN FIELD SELECTOR
# ---------------------------------------------------------

def select_relevant_fields(
    user_query: str
) -> Dict[str, Any]:
    """
    Main production-grade field selector.

    Parameters:
    -----------
    user_query : str

    Returns:
    --------
    {
        "sales_data": {
            "selected_fields": [...],
            "field_scores": [...],
            "relationships": {...}
        }
    }
    """

    logger.info(
        f"Selecting fields for query: {user_query}"
    )

    query_tokens = normalize_query(
        user_query
    )

    relevant_tables = analyze_tables(
        user_query
    )

    metadata = fetch_database_metadata()

    final_output = {}

    for table in relevant_tables:

        table_name = table["table_name"]

        table_metadata = metadata.get(
            table_name,
            {}
        )

        columns = table_metadata.get(
            "columns",
            []
        )

        column_types = table_metadata.get(
            "column_types",
            {}
        )

        scored_fields = []

        for column in columns:

            column_type = column_types.get(
                column,
                "unknown"
            )

            score = calculate_field_score(
                query_tokens=query_tokens,
                column_name=column,
                column_type=column_type
            )

            if score >= MIN_FIELD_SCORE:

                scored_fields.append({
                    "field_name": column,
                    "field_type": column_type,
                    "relevance_score": score
                })

        # -------------------------------------------------
        # SORT BY RELEVANCE
        # -------------------------------------------------

        scored_fields = sorted(
            scored_fields,
            key=lambda item: item["relevance_score"],
            reverse=True
        )

        selected_fields = [
            field["field_name"]
            for field in scored_fields[
                :MAX_FIELDS_PER_TABLE
            ]
        ]

        relationships = detect_related_columns(
            selected_fields
        )

        final_output[table_name] = {
            "selected_fields": selected_fields,
            "field_scores": scored_fields,
            "relationships": relationships
        }

    logger.info(
        f"Field selection completed successfully."
    )

    return final_output


# ---------------------------------------------------------
# LIGHTWEIGHT FIELD FETCHER
# ---------------------------------------------------------

def get_selected_fields_only(
    user_query: str
) -> Dict[str, List[str]]:
    """
    Lightweight helper function.

    Returns:
    --------
    {
        "sales_data": [
            "revenue",
            "sales_date"
        ]
    }
    """

    results = select_relevant_fields(
        user_query
    )

    return {
        table_name: value["selected_fields"]
        for table_name, value in results.items()
    }


# ---------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    query = (
        "Show monthly revenue by customer"
    )

    output = select_relevant_fields(
        query
    )

    from pprint import pprint

    pprint(output)
