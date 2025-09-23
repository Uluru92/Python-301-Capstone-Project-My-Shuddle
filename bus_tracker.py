import os
import json
from datetime import datetime
import pytz
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# -------------------- Config --------------------
load_dotenv()
NGROK_URL = os.getenv("NGROK_URL")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB_MYSHUDDLE = os.getenv("MYSQL_DB_MYSHUDDLE")

# Variables globales to scan QRs and keep wich students are in board
boarded_students = []
current_trip_id = None   # ID del viaje en curso

# Variables globales to save every route after tracking bus
coords_list = []
current_trip_file = None
trip_in_progress = False

# -------------------- Helpers --------------------
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB_MYSHUDDLE,
            port=int(MYSQL_PORT) if MYSQL_PORT else 3306
        )
    except Error as e:
        print("Error al conectar a la base de datos:", e)
        return None
    
def start_new_trip(bus_id="bus123"):
    """Inicia un nuevo viaje y crea un archivo JSON único"""
    global current_trip_file, coords_list, trip_in_progress, current_trip_id
    coords_list = []
    os.makedirs("trips", exist_ok=True)

    # Conectar a DB y crear viaje
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trips (bus_id, start_time) VALUES (%s, NOW())
    """, (bus_id,))
    conn.commit()
    
    # Obtener el trip_id generado
    current_trip_id = cur.lastrowid
    conn.close()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_trip_file = f"trips/trip_{bus_id}_{timestamp}.json"
    trip_in_progress = True
    print("🚍 Nuevo viaje iniciado:", current_trip_file)

def save_current_trip():
    """Guarda el viaje actual en el archivo JSON"""
    global current_trip_file, coords_list
    if current_trip_file and coords_list:
        with open(current_trip_file, "w") as f:
            json.dump(coords_list, f, indent=2)

# -------------------- Flask App --------------------
app = Flask(__name__)
CORS(app)  # habilita CORS para que el navegador pueda enviar POST

print("🌍 Usando URL pública de ngrok:", NGROK_URL)

# -------------------- Endpoints --------------------
@app.route("/")
def home():
    return render_template("index.html", ngrok_url=NGROK_URL)

@app.route("/scan.html")
def scan_page():
    return open("scan.html").read()

@app.route("/board_student", methods=["POST"])
def board_student():
    data = request.get_json()
    required_keys = {"student_id", "name", "parent_email", "birth_date"}
    if not data or not required_keys.issubset(data.keys()):
        return jsonify({"status": "error", "message": "Datos inválidos"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Validar si ya existe en trip_students
    cur.execute("""
        SELECT * FROM trip_students 
        WHERE trip_id = %s AND student_id = %s
    """, (current_trip_id, data["student_id"]))
    existing = cur.fetchone()

    if existing:
        conn.close()
        return jsonify({"status": "ok", "message": f"⚠️ {data['name']} ya estaba registrado"}), 200

    # Insertar en trip_students
    cur.execute("""
        INSERT INTO trip_students (trip_id, student_id, status)
        VALUES (%s, %s, 'onboard')
    """, (current_trip_id, data["student_id"]))
    conn.commit()
    conn.close()

    print(f"🎓 {data['name']} boarded the bus")
    return jsonify({"status": "ok", "message": f"✅ {data['name']} abordó el bus"}), 200

@app.route("/alight_student", methods=["POST"])
def alight_student():
    data = request.get_json()
    student_id = data.get("student_id")

    conn = get_db_connection()
    cur = conn.cursor()

    # Verificar si está onboard
    cur.execute("""
        SELECT * FROM trip_students 
        WHERE trip_id = %s AND student_id = %s AND status = 'onboard'
    """, (current_trip_id, student_id))
    student = cur.fetchone()

    if not student:
        conn.close()
        return jsonify({"status": "error", "message": "Estudiante no está a bordo"}), 404

    # Actualizar estado
    cur.execute("""
        UPDATE trip_students 
        SET status = 'dropped_off'
        WHERE trip_id = %s AND student_id = %s
    """, (current_trip_id, student_id))
    conn.commit()
    conn.close()

    print(f"⬇️ Estudiante {student_id} bajó del bus")
    return jsonify({"status": "ok", "message": f"⬇️ Estudiante {student_id} bajó del bus"}), 200


@app.route("/start_trip", methods=["POST"])
def start_trip():
    # aquí inicializas tu nuevo viaje, archivo .json, etc.
    start_new_trip()  # tu función que crea el archivo .json vacío
    return jsonify({"status": "ok"})

@app.route("/stop_trip", methods=["POST"])
def stop_trip():
    global trip_in_progress
    if not trip_in_progress:
        return jsonify({"status": "error", "message": "No hay viaje en curso"}), 400

    trip_in_progress = False
    save_current_trip()
    return jsonify({"status": "ok", "message": "Viaje detenido"}), 200

@app.route("/location", methods=["POST"])
def location():
    """Agrega coordenadas al viaje en curso con hora local de Costa Rica"""
    global coords_list, trip_in_progress
    if not trip_in_progress:
        return jsonify({"status": "error", "message": "No hay viaje en curso"}), 400

    data = request.get_json()
    required_keys = {"bus_id", "lat", "lng", "timestamp"}
    if not data or not required_keys.issubset(data.keys()):
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    # Generar timestamp en hora de Costa Rica
    cr_tz = pytz.timezone("America/Costa_Rica")
    timestamp_cr = datetime.now(cr_tz).isoformat()
    
    # Agregar timestamp correcto al diccionario
    data["timestamp"] = timestamp_cr

    coords_list.append(data)
    save_current_trip()  # Guardar en JSON

    print(f"Latitude: {data['lat']} Longitude: {data['lng']} Time: {data['timestamp']}")
    return jsonify({"status": "ok"}), 200

@app.route("/map")
def show_map():
    """Devuelve un mapa HTML con la ruta y los markers"""
    import folium
    if coords_list:
        center = (coords_list[-1]['lat'], coords_list[-1]['lng'])
    else:
        center = (10.05, -85.42)  # Hojancha (default)

    m = folium.Map(location=center, zoom_start=15)

    # Draw route
    if len(coords_list) > 1:
        path = [(c['lat'], c['lng']) for c in coords_list]
        folium.PolyLine(path, color="blue", weight=5).add_to(m)

    # Add markers
    for c in coords_list:
        folium.Marker(
            location=(c['lat'], c['lng']),
            popup=f"Bus: {c['bus_id']}<br>{c['timestamp']}"
        ).add_to(m)

    return m._repr_html_()

# -------------------- Run Flask --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
