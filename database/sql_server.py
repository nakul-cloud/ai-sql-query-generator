import os
import urllib.parse
import logging
import pyodbc
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Singleton engine instance
_engine = None

def get_connection_string():
    """
    Constructs the pyodbc connection string from environment variables.
    Supports both SQL Server Authentication and Windows Authentication (Trusted Connection).
    """
    server = os.getenv("DB_SERVER", "localhost")
    database = os.getenv("DB_DATABASE", "")
    username = os.getenv("DB_USERNAME", "")
    password = os.getenv("DB_PASSWORD", "")
    trusted = os.getenv("DB_TRUSTED_CONNECTION", "yes").lower() == "yes"
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    encrypt = os.getenv("DB_ENCRYPT", "no")
    trust_server_cert = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")

    if trusted:
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt={encrypt};TrustServerCertificate={trust_server_cert};"
    else:
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt={encrypt};TrustServerCertificate={trust_server_cert};"
    
    return conn_str

def get_engine():
    """
    Returns a singleton SQLAlchemy engine with connection pooling.
    This replaces the inefficient raw pyodbc connection per request.
    """
    global _engine
    if _engine is None:
        logger.info("Initializing SQLAlchemy engine with connection pooling.")
        conn_str = get_connection_string()
        quoted_conn_str = urllib.parse.quote_plus(conn_str)
        engine_url = f"mssql+pyodbc:///?odbc_connect={quoted_conn_str}"
        
        _engine = create_engine(
            engine_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800  # Recycle connections after 30 minutes
        )
    return _engine

def test_connection():
    """
    Tests the database connection using the SQLAlchemy engine and context manager.
    Returns (success: bool, message: str)
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Execute a simple query to verify connection
            conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to SQL Server database.")
        return True, "Successfully connected to SQL Server database!"
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False, f"Connection failed: {str(e)}"

def execute_query(sql_query):
    """
    Executes a SQL query safely using context managers and returns a pandas DataFrame.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            logger.info(f"Executing SQL Query: {sql_query.strip()}")
            df = pd.read_sql(text(sql_query), conn)
        return df, None
    except Exception as e:
        logger.error(f"SQL execution error: {str(e)}")
        return None, str(e)

def get_tables_list():
    """
    Retrieves a list of user tables in the database.
    """
    query = """
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA = 'dbo';
    """
    df, err = execute_query(query)
    if err or df is None:
        logger.warning(f"Failed to fetch tables list: {err}")
        return []
    return df['TABLE_NAME'].tolist()

def get_database_schema():
    """
    Retrieves the complete schema structure of the database, including column names, 
    data types, and table relationships, to build context for the LLM.
    """
    query = """
    SELECT 
        t.TABLE_NAME, 
        c.COLUMN_NAME, 
        c.DATA_TYPE, 
        c.IS_NULLABLE,
        CASE WHEN k.COLUMN_NAME IS NOT NULL THEN 'PK' ELSE '' END AS KeyType
    FROM INFORMATION_SCHEMA.TABLES t
    INNER JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
    LEFT JOIN (
        SELECT ku.TABLE_NAME, ku.COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
        INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc ON ku.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
        WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
    ) k ON t.TABLE_NAME = k.TABLE_NAME AND c.COLUMN_NAME = k.COLUMN_NAME
    WHERE t.TABLE_TYPE = 'BASE TABLE' AND t.TABLE_SCHEMA = 'dbo'
    ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION;
    """
    df, err = execute_query(query)
    if err or df is None:
        logger.warning(f"Failed to fetch database schema: {err}")
        return {}
    
    schema = {}
    for _, row in df.iterrows():
        table_name = row['TABLE_NAME']
        col_info = {
            'column': row['COLUMN_NAME'],
            'type': row['DATA_TYPE'],
            'nullable': row['IS_NULLABLE'],
            'key': row['KeyType']
        }
        if table_name not in schema:
            schema[table_name] = []
        schema[table_name].append(col_info)
        
    return schema

def format_schema_for_prompt(schema):
    """
    Formats the schema dictionary into a readable text description for the LLM prompt.
    """
    if not schema:
        return "No schema metadata found or database is empty."
    
    schema_str = ""
    for table_name, columns in schema.items():
        schema_str += f"Table: {table_name}\nColumns:\n"
        for col in columns:
            key_tag = f" ({col['key']})" if col['key'] else ""
            schema_str += f"  - {col['column']} ({col['type']}){key_tag}\n"
        schema_str += "\n"
    return schema_str
