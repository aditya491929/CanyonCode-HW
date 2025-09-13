# In ingest_to_sqlite.py
import pandas as pd
from sqlalchemy import create_engine
import os

DB_FILE = "canyon_code.db"

def ingest_data():
    """
    Ingests CSV data into SQLite database.
    Creates two tables: camera_feeds and table_definitions.
    """
    if os.path.exists(DB_FILE):
        print("Database file already exists. Skipping ingestion.")
        return

    try:
        engine = create_engine(f"sqlite:///{DB_FILE}")

        # Load feeds data into 'camera_feeds' table
        feeds_df = pd.read_csv("data/Table_feeds_v2.csv")
        feeds_df.to_sql("camera_feeds", engine, index=False, if_exists="replace")
        print(f"Loaded {len(feeds_df)} records into 'camera_feeds' table.")

        # Load definitions data into 'table_definitions' table
        defs_df = pd.read_csv("data/Table_defs_v2.csv")
        defs_df.to_sql("table_definitions", engine, index=False, if_exists="replace")
        print(f"Loaded {len(defs_df)} records into 'table_definitions' table.")
        
        print(f"Database '{DB_FILE}' created successfully!")
        
    except Exception as e:
        print(f"Error during data ingestion: {e}")
        return

if __name__ == "__main__":
    ingest_data()
