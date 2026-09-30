#!/bin/sh
# Usage:
#   docker run -p 8501:8501 dbgraph "postgresql+psycopg2://user:pass@host:5432/db"
#   docker run -p 8501:8501 -e DB_CONNECTION_STRING="mssql+pyodbc://user:pass@host/db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes" dbgraph
#
# Mount a host folder at /app/schema_cache to persist named schema snapshots
# across container runs, e.g. -v "${PWD}/schema_cache:/app/schema_cache"
set -e

if [ -n "$1" ]; then
    export DB_CONNECTION_STRING="$1"
fi

exec streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
