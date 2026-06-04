
"""
schema_context.py

Production-grade schema intelligence engine
for AI SQL Query Generator systems.

Responsibilities
----------------
- Dynamic schema profiling
- Statistical metadata extraction
- Semantic context generation
- LLM-ready schema formatting
- Data distribution analysis

This module intentionally avoids:
- SQL generation
- query execution orchestration
- UI logic

Author
------
AI SQL Query Generator Project
"""

import logging
from functools import lru_cache
from typing import Dict, Any, List

import pandas as pd

from sqlalchemy import text

from database.sql_server import get_engine
from analysis.field_selector import (
    select_relevant_fields
)


# ---------------------------------------------------------
# LOGGER
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

DEFAULT_SAMPLE_SIZE = 500

MAX_DISTINCT_VALUES = 25

MAX_TOP_VALUES = 5


# ---------------------------------------------------------
# SQL DATATYPE CLASSIFICATION
# ---------------------------------------------------------

NUMERIC_TYPES = {
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

DATE_TYPES = {
    "date",
    "datetime",
    "datetime2",
    "timestamp",
    "smalldatetime"
}

TEXT_TYPES = {
    "varchar",
    "nvarchar",
    "text",
    "char"
}


# ---------------------------------------------------------
# SAMPLE DATA FETCHER
# ---------------------------------------------------------

def fetch_sample_data(
    table_name: str,
    sample_size: int = DEFAULT_SAMPLE_SIZE
) -> pd.DataFrame:
    """
    Fetches random sample rows dynamically.
    """

    engine = get_engine()

    sample_query = text(f"""
        SELECT TOP {sample_size} *
        FROM [{table_name}]
        ORDER BY NEWID()
    """)

    try:

        with engine.connect() as connection:

            dataframe = pd.read_sql(
                sample_query,
                connection
            )

        return dataframe

    except Exception as error:

        logger.exception(
            f"Failed sampling table: {table_name}"
        )

        raise RuntimeError(
            f"Sample retrieval failed: {error}"
        )


# ---------------------------------------------------------
# COLUMN PROFILER
# ---------------------------------------------------------

def profile_column(
    dataframe: pd.DataFrame,
    column_name: str
) -> Dict[str, Any]:
    """
    Profiles a dataframe column dynamically.
    """

    series = dataframe[column_name]

    total_rows = len(series)

    null_count = series.isnull().sum()

    distinct_count = series.nunique(
        dropna=True
    )

    profile: Dict[str, Any] = {
        "column_name": column_name,
        "null_count": null_count,
        "null_percentage": round(
            (null_count / max(total_rows, 1)) * 100,
            2
        ),
        "distinct_count": distinct_count,
        "sample_values": []
    }

    # -----------------------------------------------------
    # SAMPLE VALUES
    # -----------------------------------------------------

    sample_values = (
        series.dropna()
        .astype(str)
        .value_counts()
        .head(MAX_TOP_VALUES)
        .index
        .tolist()
    )

    profile["sample_values"] = sample_values

    # -----------------------------------------------------
    # NUMERIC ANALYSIS
    # -----------------------------------------------------

    if pd.api.types.is_numeric_dtype(series):

        profile["semantic_type"] = "numeric"

        numeric_series = pd.to_numeric(
            series,
            errors="coerce"
        )
        if isinstance(numeric_series, pd.Series):
            numeric_series = numeric_series.dropna()
            
            if not numeric_series.empty:
                profile["statistics"] = {
                    "min": float(
                        numeric_series.min()
                    ),
                    "max": float(
                        numeric_series.max()
                    ),
                    "mean": float(
                        numeric_series.mean()
                    )
                }

    # -----------------------------------------------------
    # DATE ANALYSIS
    # -----------------------------------------------------

    elif pd.api.types.is_datetime64_any_dtype(
        series
    ):

        profile["semantic_type"] = "date"

        valid_dates = series.dropna()

        if not valid_dates.empty:

            profile["statistics"] = {
                "min_date": str(
                    valid_dates.min()
                ),
                "max_date": str(
                    valid_dates.max()
                )
            }

    # -----------------------------------------------------
    # TEXT ANALYSIS
    # -----------------------------------------------------

    else:

        profile["semantic_type"] = "categorical"

    return profile


# ---------------------------------------------------------
# TABLE CONTEXT BUILDER
# ---------------------------------------------------------

@lru_cache(maxsize=32)
def build_table_context(
    table_name: str
) -> Dict[str, Any]:
    """
    Builds rich schema context for a table.
    """

    logger.info(
        f"Building schema context for: "
        f"{table_name}"
    )

    dataframe = fetch_sample_data(
        table_name
    )

    context = {
        "table_name": table_name,
        "row_sample_size": len(dataframe),
        "columns": []
    }

    for column in dataframe.columns:

        column_profile = profile_column(
            dataframe,
            column
        )

        context["columns"].append(
            column_profile
        )

    return context


# ---------------------------------------------------------
# QUERY CONTEXT BUILDER
# ---------------------------------------------------------

def build_query_context(
    user_query: str
) -> Dict[str, Any]:
    """
    Builds full schema context
    for relevant tables and fields.
    """

    selected_fields = (
        select_relevant_fields(
            user_query
        )
    )

    final_context = {
        "query": user_query,
        "tables": []
    }

    for table_name, field_data in (
        selected_fields.items()
    ):

        table_context = build_table_context(
            table_name
        )

        selected_field_names = set(
            field_data["selected_fields"]
        )

        filtered_columns = []

        for column in (
            table_context["columns"]
        ):

            if (
                column["column_name"]
                in selected_field_names
            ):

                filtered_columns.append(
                    column
                )

        final_context["tables"].append({
            "table_name": table_name,
            "columns": filtered_columns
        })

    logger.info(
        "Query schema context generated."
    )

    return final_context


# ---------------------------------------------------------
# LLM CONTEXT FORMATTER
# ---------------------------------------------------------

def format_context_for_prompt(
    context: Dict[str, Any]
) -> str:
    """
    Converts schema context into
    LLM-friendly prompt format.
    """

    lines = []

    lines.append(
        f"User Query: "
        f"{context['query']}\n"
    )

    for table in context["tables"]:

        lines.append(
            f"Table: "
            f"{table['table_name']}"
        )

        lines.append("Columns:")

        for column in table["columns"]:

            lines.append(
                f"- {column['column_name']}"
            )

            lines.append(
                f"  Type: "
                f"{column['semantic_type']}"
            )

            lines.append(
                f"  Distinct Values: "
                f"{column['distinct_count']}"
            )

            lines.append(
                f"  Null Percentage: "
                f"{column['null_percentage']}%"
            )

            if column["sample_values"]:

                lines.append(
                    f"  Sample Values: "
                    f"{column['sample_values']}"
                )

            if "statistics" in column:

                lines.append(
                    f"  Statistics: "
                    f"{column['statistics']}"
                )

        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------
# MAIN PUBLIC API
# ---------------------------------------------------------

def generate_schema_context(
    user_query: str
) -> str:
    """
    Main public API for schema context generation.
    """

    context = build_query_context(
        user_query
    )

    return format_context_for_prompt(
        context
    )


# ---------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    query = (
        "Show monthly revenue by customer"
    )

    output = generate_schema_context(
        query
    )

    print(output)

