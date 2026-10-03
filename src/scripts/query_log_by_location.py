import os
import sys
import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

city_filter = sys.argv[1] if len(sys.argv) > 1 else None

conn = psycopg.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
with conn.cursor() as cur:
    if city_filter:
        cur.execute(
            "SELECT question, city, region, country, created_at FROM query_log WHERE city = %s ORDER BY created_at DESC",
            (city_filter,),
        )
    else:
        cur.execute("SELECT question, city, region, country, created_at FROM query_log ORDER BY created_at DESC")
    rows = cur.fetchall()

for q, city, region, country, created_at in rows:
    print(f"[{created_at}] {city}, {region}, {country}: {q}")

conn.close()