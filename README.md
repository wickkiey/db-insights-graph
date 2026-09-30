# DB Insights Graph

Explore database relationships as an interactive 3D graph. DB Insights Graph
reflects a database through SQLAlchemy, displays tables and foreign keys,
provides table-level details and sample rows, and exports the schema as
Markdown or JSON for documentation and LLM workflows.

## Features

- Interactive WebGL 3D relationship graph
- Schema, table, column, primary-key, and foreign-key discovery
- Incoming and outgoing relationship details
- Configurable sample-row previews
- Named schema snapshots for offline browsing and faster repeat loads
- Named saved connections for frequently used databases
- Markdown and JSON schema exports
- Docker support for SQLite, PostgreSQL, MySQL, and SQL Server

## Quick start

### Local installation

Prerequisites:

- Python 3.10 or newer
- A database user with metadata access and, if sample rows are enabled,
  `SELECT` access
- The client library required by your database

```powershell
git clone https://github.com/wickkiey/db-insights-graph.git
cd db-insights-graph
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Open <http://localhost:8501>, enter a SQLAlchemy connection string, optionally
give the connection a name, and select **Connect**.

To try the app without an external database:

```powershell
python create_demo_db.py
streamlit run app.py
```

Use `sqlite:///demo.sqlite` as the connection string.

### Docker

The image includes the drivers and system packages needed for SQLite,
PostgreSQL, MySQL, and SQL Server.

```powershell
docker build -t db-insights-graph .
docker run --rm -p 8501:8501 db-insights-graph
```

You can provide the connection string as an argument:

```powershell
docker run --rm -p 8501:8501 db-insights-graph `
  "postgresql+psycopg2://USER:PASSWORD@HOST:5432/DATABASE"
```

Or through an environment variable:

```powershell
docker run --rm -p 8501:8501 `
  -e DB_CONNECTION_STRING="mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE" `
  db-insights-graph
```

For SQLite, mount the directory containing the database:

```powershell
docker run --rm -p 8501:8501 `
  -v "${PWD}:/data" `
  db-insights-graph "sqlite:////data/demo.sqlite"
```

## Connection strings

DB Insights Graph accepts standard SQLAlchemy URLs.

| Database | Example |
|---|---|
| SQLite | `sqlite:///demo.sqlite` |
| PostgreSQL | `postgresql+psycopg2://USER:PASSWORD@HOST:5432/DATABASE` |
| MySQL | `mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE` |
| SQL Server | `mssql+pyodbc://USER:PASSWORD@HOST:1433/DATABASE?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes` |

When running locally, install only the driver you need if it is not already
available. The supplied `requirements.txt` includes the four supported
drivers, while SQLite is built into Python.

## Saved connections and schema snapshots

Entering a value in **Name** associates the connection with:

1. A cached schema snapshot, which avoids reflecting the database again on
   repeat visits.
2. A saved connection string, which can be loaded from the sidebar.

Select **Refresh from database** to replace an existing snapshot with a fresh
reflection. A snapshot can be opened without a live database connection, but
sample rows are available only while connected.

Local data is stored under `schema_cache/`. Persist it when using Docker by
mounting `/app/schema_cache`:

```powershell
docker run --rm -p 8501:8501 `
  -v "${PWD}/schema_cache:/app/schema_cache" `
  -e DB_CONNECTION_STRING="postgresql+psycopg2://USER:PASSWORD@HOST:5432/DATABASE" `
  -e SCHEMA_NAME="analytics" `
  db-insights-graph
```

> [!WARNING]
> Named connection strings, including embedded passwords, are stored as plain
> text in `schema_cache/_connections/connections.json`. Keep that directory
> private, do not commit it, and use saved connections only on trusted
> machines or volumes.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `DB_CONNECTION_STRING` | Pre-populates the connection field and connects on first load | Empty |
| `SCHEMA_NAME` | Name used for the saved connection and schema snapshot | Empty |
| `SCHEMA_CACHE_DIR` | Directory containing snapshots and saved connections | `schema_cache` locally, `/app/schema_cache` in Docker |

## Using the graph

- Drag to orbit the graph.
- Scroll to zoom.
- Click a table node to inspect columns, keys, relationships, and sample rows.
- Use **Fetch sample rows** and **Rows to fetch** to control data previews.
- Download the reflected schema from **Export for LLM** in Markdown or JSON.

Databases with more than 150 reflected tables display a performance warning;
rendering speed depends on browser WebGL performance and graph density.

## Project structure

| Path | Responsibility |
|---|---|
| `app.py` | Streamlit UI and application state |
| `db_introspect.py` | SQLAlchemy schema reflection and schema data models |
| `graph_builder.py` | Relationship graph construction |
| `graph3d_component.py` | Streamlit wrapper for the 3D graph |
| `graph3d_frontend/` | Static WebGL graph frontend |
| `sample_data.py` | Safe, limited sample-row queries |
| `schema_cache.py` | Named schema snapshot persistence |
| `connections.py` | Named connection persistence |
| `exporters.py` | Markdown and JSON exports |
| `create_demo_db.py` | Local SQLite demo database generator |

## Security notes

- Prefer a read-only database account with access limited to the schemas you
  intend to inspect.
- Disable **Fetch sample rows** when schema metadata is sufficient.
- Treat exported schemas and cached snapshots as potentially sensitive
  metadata.
- Connection errors hide passwords in the displayed database URL, but driver
  error details may still contain environment-specific information.
- Never commit `.streamlit/secrets.toml`, `schema_cache/`, or local database
  files; the supplied `.gitignore` excludes them.

## Troubleshooting

**The connection fails locally**

Confirm that the SQLAlchemy URL uses the correct dialect and driver, the
driver is installed, and the database accepts connections from your machine.

**SQL Server cannot find the ODBC driver**

Install Microsoft ODBC Driver 18 and verify that the URL contains
`driver=ODBC+Driver+18+for+SQL+Server`. The Docker image installs this driver
automatically.

**A cached schema is outdated**

Load the saved connection and select **Refresh from database**.

**Sample rows are unavailable**

Snapshots opened without a live connection are metadata-only. Reconnect to the
database and ensure the user has `SELECT` permission.
