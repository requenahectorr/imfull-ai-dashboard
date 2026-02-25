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
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hoteles (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(120) NOT NULL,
            ciudad VARCHAR(120),
            owner_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analisis (
            id SERIAL PRIMARY KEY,
            hotel_id INTEGER REFERENCES hoteles(id),
            fecha VARCHAR(20),
            problema_principal VARCHAR(100),
            nivel_riesgo VARCHAR(20),
            porcentaje FLOAT
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()