"""
process_query.py

Production-grade orchestration engine
for AI SQL Query Generator systems.

Responsibilities
----------------
- Coordinate AI workflow execution
- Manage pipeline stages
- Handle centralized errors
- Collect execution metadata
- Support retry workflows
- Provide execution observability

This module intentionally avoids:
- UI rendering
- direct SQL logic
- schema profiling internals

Author
------
AI SQL Query Generator Project
"""

import time
import uuid
import logging
from typing import Dict, Any

from analysis.table_analyzer import (
    analyze_tables
)

from analysis.field_selector import (
    select_relevant_fields
)

from analysis.schema_context import (
    generate_schema_context
)

from llm.query_ai import (
    generate_sql_query
)

from llm.response_generator import (
    generate_natural_language_response
)

from workflow.query_executor import (
    execute_sql_query
)


# ---------------------------------------------------------
# LOGGER CONFIGURATION
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# STAGE TIMER
# ---------------------------------------------------------

def track_stage_timing(
    start_time: float
) -> float:
    """
    Calculates execution duration.
    """

    return round(
        time.time() - start_time,
        3
    )


# ---------------------------------------------------------
# PIPELINE STAGE RUNNER
# ---------------------------------------------------------

def execute_pipeline_stage(
    stage_name: str,
    stage_function,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    Executes pipeline stage safely.
    """

    logger.info(
        f"Starting stage: {stage_name}"
    )

    start_time = time.time()

    try:

        output = stage_function(
            *args,
            **kwargs
        )

        execution_time = (
            track_stage_timing(
                start_time
            )
        )

        logger.info(
            f"Stage completed: {stage_name}"
        )

        return {
            "success": True,
            "stage_name": stage_name,
            "execution_time_seconds":
                execution_time,
            "output": output
        }

    except Exception as error:

        execution_time = (
            track_stage_timing(
                start_time
            )
        )

        logger.exception(
            f"Stage failed: {stage_name}"
        )

        return {
            "success": False,
            "stage_name": stage_name,
            "execution_time_seconds":
                execution_time,
            "error": str(error)
        }


# ---------------------------------------------------------
# MAIN QUERY PROCESSOR
# ---------------------------------------------------------

def process_user_query(
    user_query: str
) -> Dict[str, Any]:
    """
    Main orchestration pipeline.
    """

    request_id = str(uuid.uuid4())

    logger.info(
        f"Processing request: {request_id}"
    )

    pipeline_start = time.time()

    pipeline_results = {
        "request_id": request_id,
        "user_query": user_query,
        "stages": {}
    }

    try:

        # -------------------------------------------------
        # TABLE ANALYSIS
        # -------------------------------------------------

        table_stage = execute_pipeline_stage(
            "table_analysis",
            analyze_tables,
            user_query
        )

        pipeline_results["stages"][
            "table_analysis"
        ] = table_stage

        if not table_stage["success"]:

            return build_pipeline_failure(
                pipeline_results,
                "Table analysis failed."
            )

        # -------------------------------------------------
        # FIELD SELECTION
        # -------------------------------------------------

        field_stage = execute_pipeline_stage(
            "field_selection",
            select_relevant_fields,
            user_query
        )

        pipeline_results["stages"][
            "field_selection"
        ] = field_stage

        if not field_stage["success"]:

            return build_pipeline_failure(
                pipeline_results,
                "Field selection failed."
            )

        # -------------------------------------------------
        # SCHEMA CONTEXT
        # -------------------------------------------------

        schema_stage = execute_pipeline_stage(
            "schema_context",
            generate_schema_context,
            user_query
        )

        pipeline_results["stages"][
            "schema_context"
        ] = schema_stage

        if not schema_stage["success"]:

            return build_pipeline_failure(
                pipeline_results,
                "Schema context generation failed."
            )

        # -------------------------------------------------
        # SQL GENERATION
        # -------------------------------------------------

        sql_stage = execute_pipeline_stage(
            "sql_generation",
            generate_sql_query,
            user_query
        )

        pipeline_results["stages"][
            "sql_generation"
        ] = sql_stage

        if not sql_stage["success"]:

            return build_pipeline_failure(
                pipeline_results,
                "SQL generation failed."
            )

        sql_output = sql_stage[
            "output"
        ]

        if not sql_output["success"]:

            return build_pipeline_failure(
                pipeline_results,
                sql_output["error"]
            )

        generated_sql = sql_output[
            "sql_query"
        ]

        # -------------------------------------------------
        # SQL EXECUTION
        # -------------------------------------------------

        execution_stage = (
            execute_pipeline_stage(
                "query_execution",
                execute_sql_query,
                generated_sql
            )
        )

        pipeline_results["stages"][
            "query_execution"
        ] = execution_stage

        if not execution_stage["success"]:

            return build_pipeline_failure(
                pipeline_results,
                "SQL execution failed."
            )

        execution_output = execution_stage[
            "output"
        ]

        if not execution_output["success"]:

            return build_pipeline_failure(
                pipeline_results,
                execution_output["error"]
            )

        # -------------------------------------------------
        # NATURAL LANGUAGE GENERATION
        # -------------------------------------------------

        nl_result = generate_natural_language_response(
            user_query=user_query,
            sql_query=generated_sql,
            query_result=execution_output["result"]
        )

        pipeline_results["stages"].append({
            "stage": "nl_generation",
            "status": "success" if nl_result["success"] else "fallback",
            "timestamp": time.time()
        })

        # -------------------------------------------------
        # FINAL SUCCESS RESPONSE
        # -------------------------------------------------

        total_execution_time = round(
            time.time() - pipeline_start,
            3
        )

        logger.info(
            f"Pipeline completed successfully "
            f"in {total_execution_time}s"
        )

        return {
            "success": True,
            "request_id": request_id,
            "user_query": user_query,
            "generated_sql": generated_sql,
            "query_result":
                execution_output["result"],
            "nl_response":
                nl_result.get("response_text", ""),
            "execution_time_seconds":
                total_execution_time,
            "pipeline_stages":
                pipeline_results["stages"]
        }

    except Exception as error:

        logger.exception(
            "Pipeline execution failed."
        )

        return build_pipeline_failure(
            pipeline_results,
            str(error)
        )


# ---------------------------------------------------------
# FAILURE RESPONSE BUILDER
# ---------------------------------------------------------

def build_pipeline_failure(
    pipeline_results: Dict[str, Any],
    error_message: str
) -> Dict[str, Any]:
    """
    Standardized pipeline failure response.
    """

    return {
        "success": False,
        "request_id":
            pipeline_results["request_id"],
        "user_query":
            pipeline_results["user_query"],
        "error": error_message,
        "pipeline_stages":
            pipeline_results["stages"]
    }


# ---------------------------------------------------------
# LIGHTWEIGHT QUERY RUNNER
# ---------------------------------------------------------

def run_query_pipeline(
    user_query: str
) -> Dict[str, Any]:
    """
    Lightweight public pipeline API.
    """

    return process_user_query(
        user_query
    )


# ---------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    query = (
        "Show top 10 customers by revenue"
    )

    result = process_user_query(
        query
    )

    from pprint import pprint

    pprint(result)
