"""
app.py

Main Streamlit Application Entrypoint
for AI SQL Query Generator systems.

Responsibilities
----------------
- System Health Dashboard
- Database Connection Status
- Schema Exploration
- Navigation Hub

Author
------
AI SQL Query Generator Project
"""

import os
import streamlit as st
from dotenv import load_dotenv

from database.sql_server import (
    test_connection,
    get_database_schema
)

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="AI SQL Query Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# STYLING
# ---------------------------------------------------------

st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .metric-card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #334155;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #3b82f6;
    }
    .metric-label {
        font-size: 1rem;
        color: #94a3b8;
        margin-top: 8px;
    }
    .status-connected {
        color: #10b981;
        font-weight: bold;
    }
    .status-disconnected {
        color: #ef4444;
        font-weight: bold;
    }
    h1, h2, h3 {
        color: #3b82f6 !important;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# ENVIRONMENT CONFIGURATION
# ---------------------------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
gemini_ready = bool(api_key and api_key != "your_gemini_api_key_here")


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("✨ AI SQL Query Generator")
st.markdown("""
Welcome to the **AI SQL Query Generator**. This production-grade platform translates natural language into optimized Microsoft SQL Server queries.

Use the sidebar to navigate to the **Chat Assistant** or **Upload Data** tools.
""")

st.divider()


# ---------------------------------------------------------
# SYSTEM HEALTH DASHBOARD
# ---------------------------------------------------------

st.header("🎛️ System Health")

db_connected, db_msg = test_connection()
schema = get_database_schema() if db_connected else {}

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    if gemini_ready:
        st.markdown('<div class="metric-value status-connected">Active</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="metric-value status-disconnected">Missing Key</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Gemini AI Status</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    if db_connected:
        st.markdown('<div class="metric-value status-connected">Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="metric-value status-disconnected">Offline</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Database Status</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    table_count = len(schema) if schema else 0
    st.markdown(f'<div class="metric-value">{table_count}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Tables Indexed</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------
# SCHEMA EXPLORER
# ---------------------------------------------------------

st.header("📊 Database Schema Explorer")

if not db_connected:
    st.error(f"Database connection failed: {db_msg}")
elif not schema:
    st.info("No tables found in the database. Navigate to the **Upload Data** page to ingest data.")
else:
    # Display tables in an expander grid
    cols = st.columns(3)
    col_idx = 0
    
    for table_name, columns in schema.items():
        with cols[col_idx % 3]:
            with st.expander(f"📋 {table_name}", expanded=False):
                for col in columns:
                    pk_icon = "🔑 " if col.get('key') == 'PK' else "• "
                    col_type = col.get('type', 'Unknown')
                    st.markdown(f"`{pk_icon}{col['column']}` *( {col_type} )*")
        
        col_idx += 1
