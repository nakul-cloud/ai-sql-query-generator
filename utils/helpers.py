"""
helpers.py

Production-grade utility functions
for AI SQL Query Generator systems.

Responsibilities
----------------
- String manipulation
- SQL cleaning
- Common data formatting
- Shared utility functions

Author
------
AI SQL Query Generator Project
"""

import re
import logging
from typing import Optional


logger = logging.getLogger(__name__)


def clean_sql_query(
    sql_text: str
) -> str:
    """
    Cleans LLM SQL response by removing markdown blocks and whitespace.
    """

    if not sql_text:
        return ""

    cleaned = sql_text.strip()

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

    # Remove accidental explanations by just stripping again
    return cleaned.strip()
