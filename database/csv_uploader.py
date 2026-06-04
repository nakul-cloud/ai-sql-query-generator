import os
import pandas as pd
import urllib.parse
from sqlalchemy import create_engine
from database.sql_server import get_connection_string

def process_csv(file_path):
    """
    Reads a CSV file and returns a pandas DataFrame.
    Supports basic encoding fallback.
    """
    encodings = ['utf-8', 'latin1', 'utf-16', 'cp1252']
    
    for encoding in encodings:
        try:
            # Try reading with typical delimiters
            df = pd.read_csv(file_path, encoding=encoding)
            return df, None
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return None, f"Error reading CSV: {str(e)}"
            
    return None, "Unable to read file. Please ensure it's a valid CSV with correct encoding."

def upload_df_to_sql(df, table_name, if_exists='append'):
    """
    Uploads a pandas DataFrame to SQL Server.
    if_exists options: 'fail', 'replace', 'append'
    """
    try:
        # Create SQLAlchemy engine for pyodbc
        conn_str = get_connection_string()
        quoted_conn_str = urllib.parse.quote_plus(conn_str)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={quoted_conn_str}")
        
        # Write to SQL
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists=if_exists,
            index=False,
            chunksize=1000
        )
        return True, f"Successfully uploaded {len(df)} rows to table '{table_name}'."
    except Exception as e:
        return False, f"Failed to upload to SQL Server: {str(e)}"
