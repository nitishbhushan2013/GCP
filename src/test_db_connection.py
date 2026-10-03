"""
Epic 6 / Phase B / B7 prep — Confirm Cloud SQL Auth Proxy tunnel works.
"""

import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_HOST = "127.0.0.1"  # Cloud SQL Auth Proxy tunnel — local dev only
DB_PORT = 5433
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

if __name__ == "__main__":
    conn = psycopg.connect(
    host="127.0.0.1", port=5433,
    dbname="budgetsense", user="budgetsense_app", password=os.environ["DB_PASSWORD"],
)

    with conn.cursor() as cur:
        cur.execute("SELECT NOW();")
        print("Connected. DB time:", cur.fetchone()[0])

        cur.execute("SELECT COUNT(*) FROM document_sections;")
        print("document_sections row count:", cur.fetchone()[0])

        cur.execute("SELECT COUNT(*) FROM document_chunks;")
        print("document_chunks row count:", cur.fetchone()[0])

        cur.execute("""
        SELECT source_document, COUNT(*) 
        FROM document_sections 
        GROUP BY source_document;
        """)
        for row in cur.fetchall():
            print(row)

        cur.execute("""
            SELECT source_document, COUNT(*) 
            FROM document_chunks 
            GROUP BY source_document;
        """)
        for row in cur.fetchall():
          print(row)
    conn.close()