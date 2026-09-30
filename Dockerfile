FROM python:3.12-slim-bookworm

# System deps + Microsoft ODBC Driver 18 for SQL Server (msodbcsql18) so the
# same image can connect to Postgres, MySQL, SQLite and SQL Server out of the box.
# Pinned to bookworm (Debian 12) because Microsoft's package repo doesn't yet
# publish msodbcsql builds for newer Debian releases (e.g. trixie/13).
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg2 \
        apt-transport-https \
        unixodbc \
        unixodbc-dev \
        gcc \
    && curl -sSL -O https://packages.microsoft.com/keys/microsoft.asc \
    && gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg microsoft.asc \
    && rm microsoft.asc \
    && . /etc/os-release \
    && curl -sSL "https://packages.microsoft.com/config/debian/${VERSION_ID}/prod.list" \
        -o /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && apt-get purge -y --auto-remove curl gnupg2 apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

EXPOSE 8501

ENTRYPOINT ["/app/entrypoint.sh"]
