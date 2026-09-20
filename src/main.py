import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
import psycopg
from fastapi import FastAPI, Response
from pydantic import BaseModel

from rag.retrieval import retrieve
from rag.generation import generate_answer, parse_response
from fastapi.staticfiles import StaticFiles




logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("budgetsense")

app = FastAPI(title="BudgetSense-GCP")

app.mount("/static", StaticFiles(directory="static", html=True), name="static")
@app.get("/", include_in_schema=False)
def serve_ui():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT", "5432")


def get_connection():
    """
    Connects to Cloud SQL over its private IP via the Serverless VPC Access
    connector. Uses psycopg v3 (not psycopg2) - standardized project-wide
    after psycopg2-binary failed to build a wheel on Python 3.14.
    """
    return psycopg.connect(
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

class QueryRequest(BaseModel):
    question: str


@app.post("/query")
def query(request: QueryRequest):
    """
    Grounded Q&A over Federal Budget documents. Retrieval (hybrid vector +
    full-text search, RRF-fused, authority-boosted) finds the relevant
    parent sections; Gemini generates an answer constrained to only that
    retrieved text, with citations traced back to specific sources.
    """
    conn = get_connection()
    try:
        boosted, parents = retrieve(conn, request.question, top_k=5)
        raw_answer = generate_answer(request.question, parents)
        parsed = parse_response(raw_answer, parents)
    finally:
        conn.close()

    return parsed
