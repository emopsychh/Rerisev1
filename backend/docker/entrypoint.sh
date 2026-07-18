#!/bin/sh
set -e

echo "Waiting for database..."
python - <<'PY'
import os, time
import psycopg

host = os.getenv("POSTGRES_HOST", "postgres")
port = int(os.getenv("POSTGRES_PORT", "5432"))
db = os.getenv("POSTGRES_DB", "rerise")
user = os.getenv("POSTGRES_USER", "rerise")
password = os.getenv("POSTGRES_PASSWORD", "rerise")

for attempt in range(60):
    try:
        with psycopg.connect(
            host=host, port=port, dbname=db, user=user, password=password, connect_timeout=3
        ) as conn:
            conn.execute("SELECT 1")
        print("Database is ready.")
        break
    except Exception as exc:
        if attempt == 59:
            raise SystemExit(f"Database not ready: {exc}") from exc
        time.sleep(1)
PY

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
  if [ "${RUN_SEED_DEMO:-false}" = "true" ]; then
    python manage.py seed_demo
  fi
fi

exec "$@"
