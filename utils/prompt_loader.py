"""
prompt_loader.py

Production-grade prompt registry and loader
for AI SQL Query Generator systems.

Responsibilities
----------------
- Centralized prompt loading
- Prompt caching
- Dynamic prompt templating
- Prompt version management
- Prompt validation

Author
------
AI SQL Query Generator Project
"""

import os
import logging
from functools import lru_cache
from string import Template
from typing import Dict, Any


# ---------------------------------------------------------
# LOGGER
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# PROMPTS DIRECTORY
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PROMPTS_DIR = os.path.join(
    BASE_DIR,
    "prompts"
)


# ---------------------------------------------------------
# PROMPT LOADER
# ---------------------------------------------------------

@lru_cache(maxsize=32)
def load_prompt(
    prompt_name: str
) -> str:
    """
    Loads prompt dynamically from prompts directory.
    """

    file_path = os.path.join(
        PROMPTS_DIR,
        f"{prompt_name}.txt"
    )

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"Prompt not found: {file_path}"
        )

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            prompt_text = file.read()

        logger.info(
            f"Loaded prompt: {prompt_name}"
        )

        return prompt_text

    except Exception as error:

        logger.exception(
            "Prompt loading failed."
        )

        raise RuntimeError(
            f"Failed loading prompt: {error}"
        )


# ---------------------------------------------------------
# TEMPLATE RENDERER
# ---------------------------------------------------------

def render_prompt(
    prompt_name: str,
    variables: Dict[str, Any]
) -> str:
    """
    Dynamically renders prompt variables.
    """

    raw_prompt = load_prompt(
        prompt_name
    )

    try:

        template = Template(raw_prompt)

        rendered_prompt = (
            template.safe_substitute(
                variables
            )
        )

        return rendered_prompt.strip()

    except Exception as error:

        logger.exception(
            "Prompt rendering failed."
        )

        raise RuntimeError(
            f"Prompt rendering failed: {error}"
        )


# ---------------------------------------------------------
# PROMPT CACHE RESET
# ---------------------------------------------------------

def clear_prompt_cache():
    """
    Clears prompt cache dynamically.
    """

    load_prompt.cache_clear()

    logger.info(
        "Prompt cache cleared."
    )


# ---------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    prompt = render_prompt(
        "triage",
        {
            "user_query":
                "Show top customers"
        }
    )

    print(prompt)
