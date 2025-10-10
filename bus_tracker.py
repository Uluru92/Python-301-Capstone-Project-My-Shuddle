import os, json, folium, mysql.connector
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from mysql.connector import Error
from pathlib import Path

# importar modelos OOP
from models import Bus, Student, BusTracker, BusLocation

# -------------------- Config --------------------
load_dotenv()
NGROK_URL = os.getenv("NGROK_URL")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB_MYSHUDDLE = os.getenv("MYSQL_DB_MYSHUDDLE")

# -------------------- App state --------------------
class AppState:
    def __init__(self):
        self.bus_tracker = BusTracker()   # history plate
        self.current_bus = None           # Bus object cuando hay viaje 
        self.pre_scanned_students = []    # lista de Student objects antes de start_trip
        self.current_trip_id = None
        self.trip_in_progress = False
        self.current_trip_file = None

app_state = AppState()

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
    """Configura el archivo JSON y memoria para el viaje actual (usa app_state)"""
    app_state.current_bus = app_state.current_bus or Bus(plate)
    app_state.current_bus.plate = plate
    app_state.current_bus.locations = app_state.current_bus.locations or []
    os.makedirs("trips", exist_ok=True)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")      # YYYY-MM-DD
    time_str = now.strftime("%H%M%S")        # HHMMSS
    app_state.current_trip_file = f"trips/{date_str}_{plate}_trip_{time_str}.json"
    app_state.trip_in_progress = True
    print("🚍 Nuevo viaje iniciado:", app_state.current_trip_file)

# --- Get school name ---
def get_school_name_by_trip(trip):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT sc.school_name
            FROM trips t
            JOIN schools sc ON t.school_phone = sc.school_phone
            WHERE t.trip_id = %s
        """, (trip,))
        school_row = cursor.fetchone()
        school_name = school_row["school_name"] if school_row else None
        return school_name
    finally:
        cursor.close()
        conn.close()

# --- Get students in trip ---
def get_students_by_trip(trip):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT ts.student_id, CONCAT(s.first_name,' ',s.last_name) AS name,
                ts.status, ts.boarded_time, ts.boarded_lat, ts.boarded_lng, ts.dropoff_time,ts.dropoff_lat, ts.dropoff_lng
            FROM trip_students ts
            JOIN students s ON ts.student_id = s.student_id
            WHERE ts.trip_id = %s
        """, (trip,))
        students = cursor.fetchall()

        # --- Convert datetimes to strings and get floats---
    
        students_serializable = []
        for s in students:
            students_serializable.append({
            "student_id": s["student_id"],
            "name": s["name"],
            "status": s["status"],
            "boarded_time": s["boarded_time"].isoformat() if s["boarded_time"] else None,
            "boarded_lat": float(s["boarded_lat"]) if s["boarded_lat"] is not None else None,
            "boarded_lng": float(s["boarded_lng"]) if s["boarded_lng"] is not None else None,
            "dropoff_time": s["dropoff_time"].isoformat() if s["dropoff_time"] else None,
            "dropoff_lat": float(s["dropoff_lat"]) if s["dropoff_lat"] is not None else None,
            "dropoff_lng": float(s["dropoff_lng"]) if s["dropoff_lng"] is not None else None,
        })
        return students_serializable
    finally:
        cursor.close()
        conn.close()

# --- Get locations ---
def get_locations_serializable(bus):
    locations_serializable = []
    if app_state.current_bus and app_state.current_bus.locations:
        locations_serializable = [loc.to_dict() for loc in app_state.current_bus.locations]
    return locations_serializable

# --- trip data created ---
def build_trip_data(trip_id, bus, school_name, students_serializable, locations_serializable):
    return {
        "trip_id": trip_id,
        "plate": bus.plate if bus else None,
        "school": school_name,
        "locations": locations_serializable,
        "students": students_serializable
    }

# --- Get locations ---
def save_filename_trip_json(trip_data, dir_path="trips"):
    trips_dir = Path(dir_path)
    trips_dir.mkdir(exist_ok=True)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M%S")
    filename = trips_dir / f"{date_str}_{trip_data['plate']}_trip_{time_str}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(trip_data, f, ensure_ascii=False, indent=4)

    return filename

# --- Save trip ---
def save_current_trip():
    """ Save current trip in a json file, using date and timestamps"""
    if not app_state.current_trip_id:
        print("There is not current trip.")
        return

    school_name = get_school_name_by_trip(app_state.current_trip_id)
    students_serializable = get_students_by_trip(app_state.current_trip_id)
    locations_serializable = get_locations_serializable(app_state.current_bus)
    
    # --- trip data dictionary ---
    trip_data = build_trip_data(app_state.current_trip_id, app_state.current_bus, school_name, students_serializable, locations_serializable)

    # --- save JSON file ---
    filename = save_filename_trip_json(trip_data, dir_path="trips")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(trip_data, f, ensure_ascii=False, indent=4)

    print(f"🚍 Trip saved: {filename}")

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
    with open("scan.html", "r", encoding="utf-8") as f:
        return f.read()

@app.route("/board_student", methods=["POST"])
def board_student():
    """Pre-scan antes de iniciar el viaje: guarda Student objects en app_state.pre_scanned_students"""
    data = request.get_json()
    print("📱 Datos recibidos del celular:", data)
    student_id = data["student_id"]
    name = data["name"]
    lat = data.get("lat")
    lng = data.get("lng")
    timestamp = data.get("timestamp")

    # check if student is already in pre-scanned memory
    if any(str(s.student_id) == str(student_id) for s in app_state.pre_scanned_students):
        return jsonify({"status": "warning", "message": f"{name} was already scanned"}), 200

    # create Student object with atributes when scanned
    student = Student(student_id, name)
    student.status = "onboard"
    student.boarded_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # format MySQL-friendly
    student.boarded_lat = lat
    student.boarded_lng = lng
    student.dropoff_time = None
    student.dropoff_lat = None
    student.dropoff_lng = None

    # save student in pre scanned memory
    app_state.pre_scanned_students.append(student)
    print(f"🟢 Estudiante {name} registrado en memoria (pre-viaje)")
    return jsonify({
        "status": "ok",
        "student": {
            "student_id": student.student_id,
            "name": student.name,
            "status": student.status,
            "boarded_time": student.boarded_time,
            "boarded_lat": student.boarded_lat,
            "boarded_lng": student.boarded_lng,
            "dropoff_time": student.dropoff_time,
            "dropoff_lat": student.dropoff_lat,
            "dropoff_lng": student.dropoff_lng
        }
    })

@app.route("/start_trip", methods=["POST"])
def start_trip():
    """Inicia viaje: crea registro en DB, inserta trip_students y crea Bus en memoria"""
    if app_state.trip_in_progress:
        return jsonify({"status": "error", "message": "El viaje ya está en curso"}), 400

    # To improve in the future: parametrizar plate y school_phone en futuro (por ahora placeholders)
    current_plate = "BUS123"
    school_phone = "26599085"

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insertar viaje
        cursor.execute("""
            INSERT INTO trips (plate, school_phone, trip_date, departure_time)
            VALUES (%s, %s, CURDATE(), CURTIME())
        """, (current_plate, school_phone))
        conn.commit()
        current_trip_id = cursor.lastrowid
        app_state.current_trip_id = current_trip_id

        # Crear objeto Bus y añadir estudiantes escaneados
        bus = Bus(current_plate)

        for s in app_state.pre_scanned_students:

            # Insertar en trip_students (con boarded_time ya en formato MySQL)
            cursor.execute("""
                INSERT INTO trip_students (
                    trip_id, student_id, status, boarded_time, boarded_lat, boarded_lng
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (app_state.current_trip_id, s.student_id, s.status, s.boarded_time, s.boarded_lat, s.boarded_lng))

            # añadir al objeto bus
            bus.board_student(s)

        conn.commit()
        print(f"🚍 Viaje iniciado con {len(bus.students_onboard)} estudiantes (trip_id={app_state.current_trip_id})")
    except Exception as e:
        conn.rollback()
        print("Error al iniciar viaje:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    # inicializar tracking en memoria
    app_state.current_bus = bus
    app_state.bus_tracker.coords_by_bus.setdefault(current_plate, [])
    start_new_trip(plate=current_plate)
    app_state.trip_in_progress = True
    app_state.pre_scanned_students = []  # vaciamos memoria pre-viaje una vez iniciado el viaje

    return jsonify({"status": "ok", "trip_id": app_state.current_trip_id, "message": "Viaje iniciado"})

@app.route("/alight_student", methods=["POST"])
def alight_student():
    """Marca a un estudiante como dropped_off (DB) y actualiza estado local si aplica"""
    data = request.get_json()
    student_id = data.get("student_id")
    lat = data.get("lat")
    lng = data.get("lng")

    if not student_id:
        return jsonify({"status": "error", "message": "No se proporcionó student_id"}), 400

    if not app_state.trip_in_progress or not app_state.current_trip_id:
        return jsonify({
            "status": "error",
            "message": "El viaje aún no ha iniciado. No puedes bajar estudiantes."
        }), 400

    # Actualizar DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE trip_students
            SET status =  'dropped_off',
            dropoff_time = NOW(),
            dropoff_lat = %s,
            dropoff_lng = %s
        WHERE trip_id = %s AND student_id = %s
    """, (lat, lng, app_state.current_trip_id, student_id))
    conn.commit()
    cursor.close()
    conn.close()

    # --- Actualizar estado local ---
    if app_state.current_bus:
        now = datetime.now()

        # 1. Actualizar estudiante en memoria
        for s in app_state.current_bus.students_onboard:
            if str(s.student_id) == str(student_id):
                s.status = "dropped_off"
                s.dropoff_time = now.strftime("%Y-%m-%d %H:%M:%S")
                s.dropoff_lat = lat
                s.dropoff_lng = lng
                break

        # Usar timestamp recibido desde el frontend
        ts_str = data.get("timestamp")
        app_state.current_bus.locations.append(
            BusLocation(
                lat=float(lat),
                lng=float(lng),
                timestamp=ts_str,   # <- aquí usamos el timestamp del celular
                plate=app_state.current_bus.plate
            )
        )


    return jsonify({"status": "ok", "message": "Estudiante marcado como bajado"}), 200

@app.route("/get_boarded_students", methods=["GET"])
def get_boarded_students():
    """Devuelve estudiantes a bordo: si hay trip_id -> consulta DB; si no -> pre-scanned"""
    if app_state.current_trip_id:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.student_id, CONCAT(s.first_name,' ',s.last_name) AS name, ts.status
            FROM trip_students ts
            JOIN students s ON ts.student_id = s.student_id
            WHERE ts.trip_id = %s
        """, (app_state.current_trip_id,))
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(students)
    else:
        # devolver pre-scanned desde memoria
        out = []
        for s in app_state.pre_scanned_students:
            out.append({
                "student_id": s.student_id,
                "name": s.name,
                "status": getattr(s, "status", "onboard"),
                "boarded_time": getattr(s, "boarded_time", None),
                "dropoff_time": getattr(s, "dropoff_time", None)
            })
        return jsonify(out)

@app.route("/stop_trip", methods=["POST"])
def stop_trip():
    """Detiene viaje si no quedan estudiantes a bordo; actualiza DB y guarda JSON"""
    if not app_state.trip_in_progress or not app_state.current_trip_id:
        return jsonify({"status": "error", "message": "No hay viaje en curso"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar si aún quedan estudiantes a bordo
    cursor.execute("""
        SELECT COUNT(*) AS onboard_count
        FROM trip_students
        WHERE trip_id = %s AND status = 'onboard'
    """, (app_state.current_trip_id,))
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
    """, (app_state.current_trip_id,))
    conn.commit()
    cursor.close()
    conn.close()

    app_state.trip_in_progress = False
    # Guardar JSON con la info tomada desde app_state.current_bus
    save_current_trip()

    # limpiar estado actual
    app_state.current_trip_id = None
    app_state.current_bus = None
    app_state.current_trip_file = None

    return jsonify({"status": "ok", "message": "Viaje detenido"}), 200

@app.route("/location", methods=["POST"])
def location():
    """Agrega coordenadas al viaje en curso con hora local de Costa Rica"""
    if not app_state.trip_in_progress or not app_state.current_bus:
        return jsonify({"status": "error", "message": "No hay viaje en curso"}), 400

    data = request.get_json()
    required_keys = {"lat", "lng", "timestamp"}
    if not data or not required_keys.issubset(data.keys()):
        print("📱 Datos recibidos del celular (faltan claves):", data)
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    lat = data["lat"]
    lng = data["lng"]
    timestamp = data["timestamp"]

    # añadir al Bus (memoria) y al BusTracker (histórico por plate)
    app_state.current_bus.add_location(lat, lng, timestamp)
    app_state.bus_tracker.add_location(app_state.current_bus.plate, lat, lng, timestamp)

    print(f"Latitude: {lat} Longitude: {lng} Time: {timestamp} (plate={app_state.current_bus.plate})")
    return jsonify({"status": "ok"}), 200

@app.route("/map")
def show_map():
    """Devuelve un mapa HTML con la ruta y los markers (usa folium y app_state.current_bus)"""
    if app_state.current_bus and app_state.current_bus.locations:
        center = (app_state.current_bus.locations[-1].lat, app_state.current_bus.locations[-1].lng)
    else:
        center = (10.05, -85.42)  # Hojancha (default)

    m = folium.Map(location=center, zoom_start=15)

    # Draw route
    if app_state.current_bus and len(app_state.current_bus.locations) > 1:
        path = [(c.lat, c.lng) for c in app_state.current_bus.locations]
        folium.PolyLine(path, color="blue", weight=5).add_to(m)

    # Add markers
    if app_state.current_bus:
        for c in app_state.current_bus.locations:
            folium.Marker(
                location=(c.lat, c.lng),
                popup=f"Bus: {app_state.current_bus.plate}<br>{c.timestamp}"
            ).add_to(m)

    return m._repr_html_()

# -------------------- Run Flask --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)