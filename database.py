import os
import psycopg2

def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    return conn
    
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analisis (
            id SERIAL PRIMARY KEY,
            fecha VARCHAR(20),
            problema_principal VARCHAR(100),
            nivel_riesgo VARCHAR(20),
            porcentaje FLOAT
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()