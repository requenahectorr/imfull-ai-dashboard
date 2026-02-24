import sqlite3

def init_db():
    conn = sqlite3.connect("analisis.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analisis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            problema_principal TEXT,
            nivel_riesgo TEXT,
            porcentaje REAL
        )
    """)

    conn.commit()
    conn.close()