"""
Epic 6 / Phase B / B7 prep — Confirm Cloud SQL Auth Proxy tunnel works.
"""

import os
import psycopg

DB_HOST = "127.0.0.1"
DB_PORT = 5433
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

if __name__ == "__main__":
    conn = psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5,
    )
    with conn.cursor() as cur:
        cur.execute("SELECT NOW();")
        print("Connected. DB time:", cur.fetchone()[0])

        cur.execute("SELECT COUNT(*) FROM document_sections;")
        print("document_sections row count:", cur.fetchone()[0])

        cur.execute("SELECT COUNT(*) FROM document_chunks;")
        print("document_chunks row count:", cur.fetchone()[0])
    conn.close()