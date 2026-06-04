from database.sql_server import test_connection, get_connection_string
import os

print("--- DB Connection Test ---")
print(f"DB_SERVER: {os.getenv('DB_SERVER')}")
print(f"DB_DATABASE: {os.getenv('DB_DATABASE')}")
print(f"DB_TRUSTED_CONNECTION: {os.getenv('DB_TRUSTED_CONNECTION')}")
print(f"DB_DRIVER: {os.getenv('DB_DRIVER')}")
print("Connection String:", get_connection_string())

status, msg = test_connection()
print(f"Connection Status: {'SUCCESS' if status else 'FAILED'}")
print(f"Message/Error: {msg}")
