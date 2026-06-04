"""
chat_page.py

Production-grade Streamlit chat interface
for AI SQL Query Generator systems.

Responsibilities
----------------
- Handle user interactions
- Trigger AI workflow pipeline
- Display analytics results
- Render SQL insights
- Maintain chat session state

This module intentionally avoids:
- SQL generation internals
- database logic
- schema analysis internals

Author
------
AI SQL Query Generator Project
"""

import streamlit as st
import pandas as pd

from workflow.process_query import (
    process_user_query
)


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title=(
        "AI SQL Query Generator"
    ),
    page_icon="🤖",
    layout="wide"
)


# ---------------------------------------------------------
# SESSION INITIALIZATION
# ---------------------------------------------------------

if "chat_history" not in st.session_state:

    st.session_state.chat_history = []


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title(
    "🤖 AI SQL Query Generator"
)

st.markdown("""
Ask questions about your uploaded data
using natural language.
""")


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.header("⚙️ Settings")

    show_sql = st.toggle(
        "Show Generated SQL",
        value=True
    )

    show_pipeline = st.toggle(
        "Show Pipeline Details",
        value=False
    )

    clear_chat = st.button(
        "🗑️ Clear Chat"
    )

    if clear_chat:

        st.session_state.chat_history = []

        st.rerun()


# ---------------------------------------------------------
# CHAT HISTORY DISPLAY
# ---------------------------------------------------------

for message in st.session_state.chat_history:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )

        if (
            message["role"] == "assistant"
            and "dataframe" in message
        ):

            st.dataframe(
                message["dataframe"],
                use_container_width=True
            )

        if (
            show_sql
            and "sql_query" in message
        ):

            st.code(
                message["sql_query"],
                language="sql"
            )


# ---------------------------------------------------------
# USER INPUT
# ---------------------------------------------------------

user_query = st.chat_input(
    "Ask a question about your data..."
)


# ---------------------------------------------------------
# MAIN PIPELINE EXECUTION
# ---------------------------------------------------------

if user_query:

    # -----------------------------------------------------
    # STORE USER MESSAGE
    # -----------------------------------------------------

    st.session_state.chat_history.append({
        "role": "user",
        "content": user_query
    })

    with st.chat_message("user"):

        st.markdown(user_query)

    # -----------------------------------------------------
    # ASSISTANT RESPONSE
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "Analyzing your data..."
        ):

            result = process_user_query(
                user_query
            )

            # ---------------------------------------------
            # FAILURE HANDLING
            # ---------------------------------------------

            if not result["success"]:

                error_message = (
                    f"❌ Error: "
                    f"{result['error']}"
                )

                st.error(error_message)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_message
                })

            else:

                # -----------------------------------------
                # QUERY RESULTS
                # -----------------------------------------

                query_result = result[
                    "query_result"
                ]

                dataframe = pd.DataFrame(
                    query_result["rows"]
                )

                response_text = result.get(
                    "nl_response",
                    f"✅ Query executed successfully.\n\nReturned {query_result.get('row_count', 0)} rows."
                )

                st.success(response_text)

                # -----------------------------------------
                # DISPLAY DATAFRAME
                # -----------------------------------------

                if not dataframe.empty:

                    st.dataframe(
                        dataframe,
                        use_container_width=True
                    )

                # -----------------------------------------
                # GENERATED SQL
                # -----------------------------------------

                if show_sql:

                    st.subheader(
                        "Generated SQL"
                    )

                    st.code(
                        result[
                            "generated_sql"
                        ],
                        language="sql"
                    )

                # -----------------------------------------
                # EXECUTION METRICS
                # -----------------------------------------

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "Execution Time",
                        (
                            f"{result['execution_time_seconds']}s"
                        )
                    )

                with col2:

                    st.metric(
                        "Rows Returned",
                        query_result[
                            "row_count"
                        ]
                    )

                # -----------------------------------------
                # PIPELINE DETAILS
                # -----------------------------------------

                if show_pipeline:

                    st.subheader(
                        "Pipeline Details"
                    )

                    st.json(
                        result[
                            "pipeline_stages"
                        ]
                    )

                # -----------------------------------------
                # SAVE CHAT HISTORY
                # -----------------------------------------

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text,
                    "dataframe": dataframe,
                    "sql_query": result[
                        "generated_sql"
                    ]
                })
