"""
schema_manager.py

Centralized schema metadata manager
for AI SQL Query Generator systems.
"""

import logging
from functools import lru_cache
from collections import defaultdict
from typing import Dict, Any

from sqlalchemy import text

from database.sql_server import get_engine


logger = logging.getLogger(__name__)

DEFAULT_SCHEMA = "dbo"


@lru_cache(maxsize=1)
def fetch_database_metadata() -> Dict[str, Any]:
    """
    Fetches database schema metadata dynamically.
    """

    logger.info(
        "Fetching database metadata..."
    )

    engine = get_engine()

    metadata_query = text("""
        SELECT
            c.TABLE_NAME,
            c.COLUMN_NAME,
            c.DATA_TYPE,
            CASE
                WHEN k.COLUMN_NAME IS NOT NULL
                THEN 1
                ELSE 0
            END AS IS_PRIMARY_KEY
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT
                ku.TABLE_NAME,
                ku.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
            WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ) k
        ON c.TABLE_NAME = k.TABLE_NAME
        AND c.COLUMN_NAME = k.COLUMN_NAME
        WHERE c.TABLE_SCHEMA = :schema
        ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
    """)

    metadata = defaultdict(
        lambda: {
            "columns": [],
            "column_types": {},
            "primary_keys": []
        }
    )

    try:

        with engine.connect() as connection:

            result = connection.execute(
                metadata_query,
                {"schema": DEFAULT_SCHEMA}
            )

            for row in result:

                table_name = row.TABLE_NAME
                column_name = row.COLUMN_NAME
                data_type = row.DATA_TYPE
                is_primary_key = row.IS_PRIMARY_KEY

                metadata[table_name][
                    "columns"
                ].append(column_name)

                metadata[table_name][
                    "column_types"
                ][column_name] = data_type

                if is_primary_key:

                    metadata[table_name][
                        "primary_keys"
                    ].append(column_name)

        logger.info(
            "Database metadata loaded successfully."
        )

        return dict(metadata)

    except Exception as error:

        logger.exception(
            "Metadata retrieval failed."
        )

        raise RuntimeError(
            f"Failed to fetch schema metadata: {error}"
        )
