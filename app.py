from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from database import get_connection, create_tables, create_default_hotel

app = Flask(__name__)
app.secret_key = "clave_super_secreta_cambiar_en_produccion"

# Crear tablas y hotel demo al iniciar
create_tables()
create_default_hotel()

# ===============================
# MOTOR DE ANÁLISIS
# ===============================

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

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM hoteles WHERE nombre = %s;", ("Hotel Demo",))
    hotel = cursor.fetchone()
    hotel_id = hotel[0]

    cursor.execute("""
        INSERT INTO analisis (hotel_id, fecha, problema_principal, nivel_riesgo, porcentaje)
        VALUES (%s, %s, %s, %s, %s)
    """, (hotel_id, fecha, problema_principal, nivel_riesgo, porcentaje_principal))

    conn.commit()
    cursor.close()
    conn.close()

    return informe


# ===============================
# RUTAS
# ===============================

@app.route("/", methods=["GET", "POST"])
def index():
    informe = ""

    if request.method == "POST":
        texto_reseñas = request.form["reseñas"]
        informe = analizar_reseñas_web(texto_reseñas)

    return render_template("index.html", informe=informe)


@app.route("/dashboard")
def dashboard():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT fecha, problema_principal, nivel_riesgo, porcentaje
        FROM analisis
        ORDER BY id DESC
    """)
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

    conteo = {}
    for fila in ultimos:
        problema = fila[0]
        conteo[problema] = conteo.get(problema, 0) + 1

    problema_reciente = max(conteo, key=conteo.get) if conteo else "N/A"

    cursor.execute("""
        SELECT problema_principal, COUNT(*)
        FROM analisis
        GROUP BY problema_principal
    """)
    datos_grafico = cursor.fetchall()

    labels = [fila[0] for fila in datos_grafico]
    valores = [fila[1] for fila in datos_grafico]

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        datos=datos,
        total_analisis=total_analisis,
        promedio=promedio,
        ultimo_nivel=ultimo_nivel,
        problema_frecuente=problema_frecuente,
        frecuencia_problema=frecuencia_problema,
        problema_reciente=problema_reciente,
        labels=labels,
        valores=valores
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (email, password_hash)
            VALUES (%s, %s)
            ON CONFLICT (email) DO NOTHING;
        """, (email, password))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, password_hash
            FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and user[1] == password:
            session["user_id"] = user[0]
            return redirect(url_for("dashboard"))
        else:
            return "Credenciales incorrectas"

    return render_template("login.html")


if __name__ == "__main__":
    app.run()