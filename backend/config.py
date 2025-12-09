import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# Database URL (SQLite for local, Azure SQL later)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dq_metadata.db")

# Databricks connection details
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
DATABRICKS_JOB_ID = os.getenv("DATABRICKS_JOB_ID")

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "dq-results")

print("HOST:", DATABRICKS_HOST)
print("PATH:", DATABRICKS_HTTP_PATH)
print("TOKEN:", "SET" if DATABRICKS_TOKEN else None)

