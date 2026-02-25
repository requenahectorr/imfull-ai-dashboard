import os
import psycopg2

def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    return conn