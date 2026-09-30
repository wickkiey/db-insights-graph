# DB Relations Graph

Streamlit app: paste a SQLAlchemy connection string, explore your schema as a
clickable graph, inspect table details + sample rows, and export the schema as
Markdown/JSON for LLM prompts.

## Run

```powershell
pip install -r requirements.txt
# also install a driver for your DB dialect, e.g.: pip install psycopg2-binary
streamlit run app.py
```

Enter a SQLAlchemy connection string (e.g. `sqlite:///mydb.sqlite` or
`postgresql+psycopg2://user:pass@host/db`) in the sidebar and click Connect.

## Run with Docker

The image bundles drivers/clients for SQLite, PostgreSQL, MySQL and SQL Server
(via Microsoft's `msodbcsql18` ODBC driver), so no extra setup is needed per dialect.

```powershell
docker build -t dbgraph .

# pass the connection string as a docker run argument
docker run -p 8501:8501 dbgraph "postgresql+psycopg2://user:pass@host:5432/db"

# ...or via an env var (useful with docker-compose / secrets)
docker run -p 8501:8501 -e DB_CONNECTION_STRING="postgresql+psycopg2://user:pass@host:5432/db" dbgraph

# SQL Server example
docker run -p 8501:8501 dbgraph "mssql+pyodbc://user:pass@host:1433/db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

# MySQL example
docker run -p 8501:8501 dbgraph "mysql+pymysql://user:pass@host:3306/db"

# SQLite example (mount the file into the container)
docker run -p 8501:8501 -v "${PWD}:/data" dbgraph "sqlite:////data/mydb.sqlite"
```

Then open http://localhost:8501. If no connection string is supplied, the app
starts with an empty sidebar and you can enter one manually.

## Caching a reflected schema

Enter a **Schema name** in the sidebar alongside the connection string. On
Connect, if a saved copy with that name already exists it's loaded from disk
instead of re-querying the database; otherwise it's reflected once and saved.
Use **Refresh from database** to force a fresh reflect and overwrite the saved
copy. Previously saved schemas also show up in a **Saved schemas** picker so
you can reopen them later without a connection string (sample rows need a live
connection, though).

Mount a host folder at `/app/schema_cache` so saved schemas survive container
restarts:

```powershell
docker run -p 8501:8501 -v "${PWD}/schema_cache:/app/schema_cache" dbgraph "postgresql+psycopg2://user:pass@host:5432/db"
```

