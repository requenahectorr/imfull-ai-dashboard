from database import init_db
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)
init_db()

# ====== MOTOR DE ANÁLISIS (versión simplificada web) ======

def analizar_reseñas_web(texto_reseñas):

    reseñas = [r.strip() for r in texto_reseñas.split("\n") if r.strip() != ""]

    if not reseñas:
        return "No se han introducido reseñas."

    sentimientos = {"positivas": 0, "negativas": 0, "neutras": 0}

    problemas = {
        "cancelaciones": ["cancel", "cancelaron"],
        "retrasos": ["tarde", "espera"],
        "trato": ["antipático", "mal trato"],
        "temperatura": ["calor", "aire", "temperatura"]
    }

    conteo_problemas = {k: 0 for k in problemas.keys()}

    for reseña in reseñas:
        texto = reseña.lower()
        detectado_negativo = False

        for categoria, palabras in problemas.items():
            for palabra in palabras:
                if palabra in texto:
                    conteo_problemas[categoria] += 1
                    sentimientos["negativas"] += 1
                    detectado_negativo = True
                    break
            if detectado_negativo:
                break

        if not detectado_negativo:
            if "excelente" in texto or "increíble" in texto or "muy buen" in texto:
                sentimientos["positivas"] += 1
            else:
                sentimientos["neutras"] += 1

    total = len(reseñas)
    porcentaje_negativas = (sentimientos["negativas"] / total) * 100

    problema_principal = max(conteo_problemas, key=conteo_problemas.get)
    cantidad_principal = conteo_problemas[problema_principal]
    porcentaje_principal = (cantidad_principal / total) * 100 if total > 0 else 0

    if porcentaje_principal <= 10:
        nivel_riesgo = "BAJO"
    elif porcentaje_principal <= 20:
        nivel_riesgo = "MODERADO"
    elif porcentaje_principal <= 30:
        nivel_riesgo = "ALTO"
    else:
        nivel_riesgo = "CRÍTICO"

    fecha = datetime.now().strftime("%d/%m/%Y")

    informe = f"""
    <h2>SISTEMA DE MONITORIZACIÓN OPERATIVA – HOTEL TGN</h2>
    <p><strong>Fecha:</strong> {fecha}</p>
    <p><strong>Total reseñas:</strong> {total}</p>
    <p><strong>Problema prioritario:</strong> {problema_principal.capitalize()} ({porcentaje_principal:.1f}%)</p>
    <p><strong>Nivel de riesgo:</strong> {nivel_riesgo}</p>
    """
    import sqlite3

    conn = sqlite3.connect("analisis.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO analisis (fecha, problema_principal, nivel_riesgo, porcentaje)
        VALUES (?, ?, ?, ?)
    """, (fecha, problema_principal, nivel_riesgo, porcentaje_principal))

    conn.commit()
    conn.close()

    return informe


# ====== RUTA WEB ======

@app.route("/", methods=["GET", "POST"])
def index():
    informe = ""

    if request.method == "POST":
        texto_reseñas = request.form["reseñas"]
        informe = analizar_reseñas_web(texto_reseñas)

    return render_template("index.html", informe=informe)

@app.route("/dashboard")
def dashboard():
    import sqlite3

    conn = sqlite3.connect("analisis.db")
    cursor = conn.cursor()

    cursor.execute("SELECT fecha, problema_principal, nivel_riesgo, porcentaje FROM analisis ORDER BY id DESC")
    datos = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM analisis")
    total_analisis = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(porcentaje) FROM analisis")
    promedio = cursor.fetchone()[0]

    cursor.execute("SELECT nivel_riesgo FROM analisis ORDER BY id DESC LIMIT 1")
    ultimo = cursor.fetchone()
    ultimo_nivel = ultimo[0] if ultimo else "N/A"

    cursor.execute("""
        SELECT problema_principal, COUNT(*) as total
        FROM analisis
        GROUP BY problema_principal
        ORDER BY total DESC
        LIMIT 1
    """)
    resultado = cursor.fetchone()
    if resultado:
        problema_frecuente = resultado[0]
        frecuencia_problema = resultado[1]
    else:
        problema_frecuente = "N/A"
        frecuencia_problema = 0

    cursor.execute("""
    SELECT problema_principal
    FROM analisis
    ORDER BY id DESC
    LIMIT 3
    """)

    ultimos = cursor.fetchall()

    # Contar cuál se repite más en los últimos 3
    conteo = {}
    for fila in ultimos:
        problema = fila[0]
        conteo[problema] = conteo.get(problema, 0) + 1

    if conteo:
        problema_reciente = max(conteo, key=conteo.get)
    else:
        problema_reciente = "N/A"
        
    conn.close()

    return render_template(
        "dashboard.html",
        datos=datos,
        total_analisis=total_analisis,
        promedio=promedio,
        ultimo_nivel=ultimo_nivel,
        problema_frecuente=problema_frecuente,
        frecuencia_problema=frecuencia_problema,
        problema_reciente=problema_reciente
    )

if __name__ == "__main__":
    app.run()