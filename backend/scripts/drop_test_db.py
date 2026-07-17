import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

conn = psycopg.connect(
    dbname="postgres",
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5432"),
)
conn.autocommit = True
db_name = f"test_{os.getenv('POSTGRES_DB', 'rerise')}"
with conn.cursor() as cur:
    cur.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s",
        (db_name,),
    )
    cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
print(f"Dropped {db_name}")
