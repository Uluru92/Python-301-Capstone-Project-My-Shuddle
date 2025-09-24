import os
import json
from datetime import datetime
import pytz
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from pathlib import Path

# -------------------- Config --------------------
load_dotenv()
NGROK_URL = os.getenv("NGROK_URL")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB_MYSHUDDLE = os.getenv("MYSQL_DB_MYSHUDDLE")

# Variables globales
scanned_students = []  
current_trip_id = None
trip_in_progress = False
coords_list = []
current_trip_file = None
current_plate = None

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
    
def start_new_trip(plate="BUS123"):
    """Configura el archivo JSON y memoria para el viaje actual"""
    global current_trip_file, coords_list, trip_in_progress
    coords_list = []
    os.makedirs("trips", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_trip_file = f"trips/trip_{plate}_{timestamp}.json"
    trip_in_progress = True
    print("🚍 Nuevo viaje iniciado:", current_trip_file)

def save_current_trip():
    """Guarda el viaje actual en un archivo JSON, con timestamps serializables"""
    global current_trip_id, current_plate

    if not current_trip_id:
        print("No hay viaje activo para guardar.")
        return

    # --- Obtener estudiantes del viaje ---
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ts.student_id, CONCAT(s.first_name,' ',s.last_name) AS name,
               ts.status, ts.boarded_at, ts.dropoff_time
        FROM trip_students ts
        JOIN students s ON ts.student_id = s.student_id
        WHERE ts.trip_id = %s
    """, (current_trip_id,))
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    # --- Convertir datetimes a strings ---
    students_serializable = []
    for s in students:
        students_serializable.append({
            "student_id": s["student_id"],
            "name": s["name"],
            "status": s["status"],
            "boarded_at": s["boarded_at"].isoformat() if s["boarded_at"] else None,
            "dropoff_time": s["dropoff_time"].isoformat() if s["dropoff_time"] else None
        })

    # --- Preparar datos del viaje ---
    trip_data = {
        "trip_id": current_trip_id,
        "plate": current_plate,
        "locations": coords_list,
        "students": students_serializable
    }

    # --- Guardar en JSON ---
    trips_dir = Path("trips")
    trips_dir.mkdir(exist_ok=True)
    filename = trips_dir / f"trip_{current_plate}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(trip_data, f, ensure_ascii=False, indent=4)

    print(f"🚍 Viaje guardado: {filename}")

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
    global scanned_students

    data = request.get_json()
    print("📱 Datos recibidos del celular:", data)
    student_id = data["student_id"]
    name = data["name"]

    # Verificar si ya está en memoria
    if any(s["student_id"] == student_id for s in scanned_students):
        return jsonify({"status": "warning", "message": f"{name} ya está escaneado"}), 200

    student_entry = {
        "student_id": student_id,
        "name": name,
        "status": "onboard",
         "boarded_at": datetime.now().isoformat(),  # 👈 aquí guardamos hora de abordaje
        "dropoff_time": None
    }

    scanned_students.append(student_entry)
    print(f"🟢 Estudiante {name} registrado en memoria (pre-viaje)")
    return jsonify({"status": "ok", "student": student_entry})

@app.route("/alight_student", methods=["POST"])
def alight_student():
    global trip_in_progress, current_trip_id
    data = request.get_json()
    student_id = data.get("student_id")

    if not student_id:
        return jsonify({"status": "error", "message": "No se proporcionó student_id"}), 400

    if not trip_in_progress or not current_trip_id:
        # Si aún no hay viaje en curso
        return jsonify({
            "status": "error",
            "message": "El viaje aún no ha iniciado. No puedes bajar estudiantes."
        }), 400

    # --- Aquí sigue tu lógica actual para marcar al estudiante como dropped_off ---
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE trip_students
        SET status = 'dropped_off',
            dropoff_time = NOW()
        WHERE trip_id = %s AND student_id = %s
    """, (current_trip_id, student_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "ok", "message": "Estudiante marcado como bajado"}), 200

@app.route("/start_trip", methods=["POST"])
def start_trip():
    global current_trip_id, scanned_students, trip_in_progress,current_plate

    if trip_in_progress:
        return jsonify({"status": "error", "message": "El viaje ya está en curso"}), 400

    current_plate  = "BUS123" 
    school_phone = "26599085" 

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insertar viaje
        cursor.execute("""
            INSERT INTO trips (plate, school_phone, trip_date, departure_time)
            VALUES (%s, %s, CURDATE(), CURTIME())
        """, (current_plate, school_phone))
        current_trip_id = cursor.lastrowid

        # Guardar estudiantes en DB con boarded_at
        for s in scanned_students:
            cursor.execute("""
                INSERT INTO trip_students (trip_id, student_id, status, boarded_at)
                VALUES (%s, %s, 'onboard', %s)
            """, (current_trip_id, s["student_id"], s["boarded_at"]))

        conn.commit()
        print(f"🚍 Viaje iniciado con {len(scanned_students)} estudiantes (trip_id={current_trip_id})")
    except Exception as e:
        conn.rollback()
        print("Error al iniciar viaje:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    start_new_trip(plate=current_plate)
    trip_in_progress = True
    scanned_students = []  # vaciamos memoria pre-viaje

    return jsonify({"status": "ok", "trip_id": current_trip_id, "message": "Viaje iniciado"})
    
@app.route("/get_boarded_students", methods=["GET"])
def get_boarded_students():
    global current_trip_id, scanned_students
    if current_trip_id:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.student_id, CONCAT(s.first_name,' ',s.last_name) AS name, ts.status
            FROM trip_students ts
            JOIN students s ON ts.student_id = s.student_id
            WHERE ts.trip_id = %s
        """, (current_trip_id,))
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(students)
    else:
        return jsonify(scanned_students)

@app.route("/stop_trip", methods=["POST"])
def stop_trip():
    global trip_in_progress, current_trip_id
    if not trip_in_progress or not current_trip_id:
        return jsonify({"status": "error", "message": "No hay viaje en curso"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar si aún quedan estudiantes a bordo
    cursor.execute("""
        SELECT COUNT(*) AS onboard_count
        FROM trip_students
        WHERE trip_id = %s AND status = 'onboard'
    """, (current_trip_id,))
    onboard_count = cursor.fetchone()["onboard_count"]

    if onboard_count > 0:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "No se puede detener el viaje: aún hay estudiantes a bordo"}), 400

    # ✅ Si ya no quedan estudiantes, cerrar viaje
    cursor.execute("""
        UPDATE trips
        SET arrival_time = CURTIME()
        WHERE trip_id = %s
    """, (current_trip_id,))
    conn.commit()
    cursor.close()
    conn.close()

    trip_in_progress = False
    save_current_trip()
    current_trip_id = None

    return jsonify({"status": "ok", "message": "Viaje detenido"}), 200

@app.route("/location", methods=["POST"])
def location():
    """Agrega coordenadas al viaje en curso con hora local de Costa Rica"""
    global coords_list, trip_in_progress
    if not trip_in_progress:
        return jsonify({"status": "error", "message": "No hay viaje en curso"}), 400

    data = request.get_json()
    required_keys = {"lat", "lng", "timestamp"}
    
    if not data or not required_keys.issubset(data.keys()):
        print("📱 Datos recibidos del celular (faltan claves):", data)
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    coords_list.append(data)

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
            popup=f"Bus: {c['plate']}<br>{c['timestamp']}"
        ).add_to(m)

    return m._repr_html_()

# -------------------- Run Flask --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)