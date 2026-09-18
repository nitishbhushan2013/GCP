import os
import psycopg

conn = psycopg.connect(
    host="127.0.0.1", port=5433,
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
)
with conn.cursor() as cur:
    cur.execute("DELETE FROM document_chunks;")
    cur.execute("DELETE FROM document_sections;")
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM document_sections;")
    print("sections:", cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM document_chunks;")
    print("chunks:", cur.fetchone()[0])
conn.close()