import os
import re
# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import google.generativeai as genai
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

from database.sql_server import (
    test_connection,
    get_database_schema,
    format_schema_for_prompt,
    execute_query
)

# Page Configuration
st.set_page_config(
    page_title="AI SQL Query Generator",
    page_icon="✨",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stTextInput>div>div>input {
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    .stTextArea>div>div>textarea {
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.5);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.5);
        color: #ffffff;
    }
    .card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #334155;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .schema-card {
        background-color: #182235;
        border-left: 4px solid #3b82f6;
        border-radius: 4px;
        padding: 12px;
        margin-bottom: 12px;
        font-family: monospace;
        font-size: 0.9em;
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

# Load environment variables
load_dotenv()

# Initialize Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key and api_key != "your_gemini_api_key_here":
    genai.configure(api_key=api_key)
    gemini_ready = True
else:
    gemini_ready = False

# Sidebar: DB Connection Status and Table Schema Explorer
st.sidebar.markdown("## ⚙️ Connections & Metadata")

# Test DB Connection
db_connected, db_msg = test_connection()
schema: dict = {}
if db_connected:
    st.sidebar.markdown("### Database Status: <span class='status-connected'>● Connected</span>", unsafe_allow_html=True)
    
    # Load Schema
    schema = get_database_schema()
    st.sidebar.markdown("### 📊 Database Schema Explorer")
    if schema:
        for table_name, columns in schema.items():
            with st.sidebar.expander(f"📋 {table_name}", expanded=False):
                for col in columns:
                    pk_icon = "🔑 " if col['key'] == 'PK' else ""
                    st.markdown(f"`{pk_icon}{col['column']}` ({col['type']})")
    else:
        st.sidebar.warning("No tables found in the database. Go to **Upload Data** page to import CSV files.")
else:
    st.sidebar.markdown("### Database Status: <span class='status-disconnected'>● Disconnected</span>", unsafe_allow_html=True)
    st.sidebar.error(f"Error details: {db_msg}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 Gemini AI Status")
if gemini_ready:
    st.sidebar.markdown("<span class='status-connected'>● Active & Ready</span>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("<span class='status-disconnected'>● Configuration Missing</span>", unsafe_allow_html=True)
    st.sidebar.info("Please set your `GEMINI_API_KEY` in the `.env` file to enable AI-powered SQL generation.")

# Main Page UI
st.title("✨ AI-Powered SQL Server Query Assistant")
st.markdown("Translate natural language questions into valid T-SQL queries, execute them, and view real-time data visualisations.")

if not gemini_ready:
    st.warning("⚠️ **Gemini API Key is not set.** Please configure your `GEMINI_API_KEY` in the `.env` file at the root of the project to begin translating prompts into SQL.")

# Quick Start Hints
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("💡 Ask your database anything")
user_prompt = st.text_area(
    "Describe what data you want to retrieve in plain English:",
    placeholder="e.g., Get the top 10 rows from the sales table ordered by transaction date descending, or List the average salary of employees by department...",
    height=120
)
st.markdown('</div>', unsafe_allow_html=True)

# Main Action Buttons
generate_clicked = st.button("🧠 Generate SQL Query", disabled=not gemini_ready or not db_connected)

if generate_clicked:
    if not user_prompt.strip():
        st.error("Please enter a prompt first.")
    else:
        with st.spinner("Analyzing database schema and crafting SQL query..."):
            try:
                # Retrieve schema context
                schema_context = format_schema_for_prompt(schema)
                
                # Setup LLM instructions
                system_prompt = f"""
You are an expert T-SQL developer for Microsoft SQL Server.
Given the database schema details below, translate the user's request into a single executable T-SQL query.

DATABASE SCHEMA:
{schema_context}

USER REQUEST:
{user_prompt}

CRITICAL RULES:
1. Always prefix table names with the 'dbo' schema if applicable (e.g. dbo.table_name).
2. Generate ONLY valid MS SQL Server T-SQL syntax (use TOP instead of LIMIT, etc.).
3. Output your response EXACTLY inside these two tags:
   <sql>
   YOUR SQL QUERY HERE
   </sql>
   <explanation>
   A concise summary explanation of what the query does and how it filters/joins tables.
   </explanation>
4. Do not include any markdown format tags like ```sql inside the tags.
"""
                
                # Generate query
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(system_prompt)
                response_text = response.text
                
                # Parse response
                sql_match = re.search(r'<sql>(.*?)</sql>', response_text, re.DOTALL)
                explanation_match = re.search(r'<explanation>(.*?)</explanation>', response_text, re.DOTALL)
                
                if sql_match:
                    sql_query = sql_match.group(1).strip()
                    explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided."
                    
                    # Store generated query in session state
                    st.session_state['generated_sql'] = sql_query
                    st.session_state['sql_explanation'] = explanation
                else:
                    st.error("Could not parse SQL query from AI response. Please try refining your prompt.")
                    st.write(response_text)
                    
            except Exception as e:
                st.error(f"AI Generation failed: {str(e)}")

# Display AI Results
if 'generated_sql' in st.session_state:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🤖 Generated SQL Query")
    
    # Text area for user editing before execution
    sql_editor = st.text_area(
        "Edit the SQL if needed:",
        value=st.session_state['generated_sql'],
        height=180,
        key="editable_sql"
    )
    
    # Display explanation
    st.markdown("##### 💡 Logic Explanation")
    st.info(st.session_state['sql_explanation'])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Run query
    col1, col2 = st.columns([1, 4])
    with col1:
        run_clicked = st.button("🚀 Run Query")
        
    if run_clicked:
        with st.spinner("Executing query on SQL Server..."):
            df, error = execute_query(sql_editor)
            
            if error:
                st.error(f"❌ SQL Execution Error:\n\n{error}")
            elif df is not None:
                st.success(f"✅ Success! Fetched {len(df)} rows.")
                
                # Show results in a clean table
                st.subheader("📊 Query Results")
                st.dataframe(df, use_container_width=True)
                
                # Download CSV option
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv_data,
                    file_name="query_results.csv",
                    mime="text/csv"
                )
