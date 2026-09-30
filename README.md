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
