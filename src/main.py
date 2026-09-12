import os
import logging
from datetime import datetime, timezone

import psycopg2
from fastapi import FastAPI, Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("budgetsense")

app = FastAPI(title="BudgetSense-GCP Health Check")

# Cloud Run injects these as env vars, each mapped to a Secret Manager secret
# (db-host, db-name, db-user, db-password) — never hardcoded, never in a .env
# file that gets built into the image.
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT", "5432")


def get_connection():
    """
    Connects to Cloud SQL over its private IP. This only works because Cloud
    Run has the Serverless VPC Access connector (budgetsense-connector)
    attached, routing traffic into the private subnet where Cloud SQL lives.
    No public IP is involved anywhere in this path.
    """
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5,
    )


@app.get("/")
def root():
    return {"service": "budgetsense-gcp", "status": "running"}


@app.get("/health")
def health(response: Response):
    """
    Proves the full private-networking path end to end: Cloud Run -> VPC
    connector -> private subnet -> Cloud SQL private IP. A live round-trip
    query (SELECT NOW()) is used rather than just checking the TCP port,
    so a healthy response means the database is actually queryable, not
    merely reachable.
    """
    result = {
        "status": "unknown",
        "db_connected": False,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT NOW();")
                db_time = cur.fetchone()[0]
            result["status"] = "healthy"
            result["db_connected"] = True
            result["db_time"] = db_time.isoformat()
        finally:
            conn.close()
    except Exception as exc:
        logger.exception("Health check DB connection failed")
        result["status"] = "unhealthy"
        result["error"] = str(exc)
        response.status_code = 503

    return result