"""
triage.py

Production-grade semantic intent classifier
for AI SQL Query Generator systems.

Responsibilities
----------------
- Semantic intent classification
- AI-driven workflow routing
- Structured output validation
- Dynamic prompt execution

Author
------
AI SQL Query Generator Project
"""

import os
import json
import logging
from typing import Dict, Any

import google.generativeai as genai

from dotenv import load_dotenv

from utils.prompt_loader import (
    render_prompt
)


# ---------------------------------------------------------
# ENVIRONMENT CONFIGURATION
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# LOGGER
# ---------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# GEMINI CONFIGURATION
# ---------------------------------------------------------

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

if not GEMINI_API_KEY:

    raise ValueError(
        "GEMINI_API_KEY not found."
    )

genai.configure(
    api_key=GEMINI_API_KEY
)


# ---------------------------------------------------------
# MODEL CONFIGURATION
# ---------------------------------------------------------

MODEL_NAME = "gemini-2.5-flash-lite"

TEMPERATURE = 0.0


# ---------------------------------------------------------
# MODEL INITIALIZATION
# ---------------------------------------------------------

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config={
        "temperature": TEMPERATURE
    }
)


# ---------------------------------------------------------
# VALID INTENTS
# ---------------------------------------------------------

VALID_INTENTS = {
    "DATA_QUERY",
    "GENERAL_CHAT",
    "UNSAFE_REQUEST",
    "UNKNOWN"
}


# ---------------------------------------------------------
# JSON CLEANER
# ---------------------------------------------------------

def clean_json_response(
    response_text: str
) -> str:
    """
    Cleans malformed JSON responses.
    """

    cleaned = response_text.strip()

    cleaned = cleaned.replace(
        "```json",
        ""
    )

    cleaned = cleaned.replace(
        "```",
        ""
    )

    return cleaned.strip()


# ---------------------------------------------------------
# RESPONSE VALIDATOR
# ---------------------------------------------------------

def validate_classification(
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validates semantic classification output.
    """

    intent = result.get(
        "intent",
        "UNKNOWN"
    )

    confidence = result.get(
        "confidence",
        0.0
    )

    reason = result.get(
        "reason",
        ""
    )

    if intent not in VALID_INTENTS:

        raise ValueError(
            f"Invalid intent: {intent}"
        )

    return {
        "success": True,
        "intent": intent,
        "confidence": float(confidence),
        "reason": reason
    }


# ---------------------------------------------------------
# MAIN TRIAGE ENGINE
# ---------------------------------------------------------

def classify_user_query(
    user_query: str
) -> Dict[str, Any]:
    """
    Production-grade semantic intent classifier.
    """

    logger.info(
        f"Classifying query: {user_query}"
    )

    try:

        # -------------------------------------------------
        # DYNAMIC PROMPT RENDERING
        # -------------------------------------------------

        final_prompt = render_prompt(
            prompt_name="triage",
            variables={
                "user_query": user_query
            }
        )

        # -------------------------------------------------
        # GEMINI INFERENCE
        # -------------------------------------------------

        response = model.generate_content(
            final_prompt
        )

        raw_output = response.text.strip()

        cleaned_output = clean_json_response(
            raw_output
        )

        # -------------------------------------------------
        # PARSE JSON RESPONSE
        # -------------------------------------------------

        parsed_output = json.loads(
            cleaned_output
        )

        validated_output = (
            validate_classification(
                parsed_output
            )
        )

        logger.info(
            f"Intent classified: "
            f"{validated_output['intent']}"
        )

        return validated_output

    except Exception as error:

        logger.exception(
            "Semantic triage failed."
        )

        return {
            "success": False,
            "intent": "UNKNOWN",
            "confidence": 0.0,
            "reason": str(error)
        }


# ---------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------

if __name__ == "__main__":

    queries = [
        "Show top customers by revenue",
        "Hello",
        "Drop all tables"
    ]

    for query in queries:

        result = classify_user_query(
            query
        )

        print("\n")
        print(query)
        print(result)
