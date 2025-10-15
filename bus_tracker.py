import os, json, folium, mysql.connector, secrets
from datetime import datetime, timedelta
from flask import Flask, request, session, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from mysql.connector import Error
from pathlib import Path
from folium.plugins import MarkerCluster


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

# --- Costa Rica timezone ---
def to_cr_time_str(ts_str):
    """Convierte timestamp UTC (con Z) a hora Costa Rica en formato ISO sin Z"""
    if ts_str is None:
        return None
    # parse UTC
    utc_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    # restar 6 horas
    cr_dt = utc_dt - timedelta(hours=6)
    # formato ISO sin Z
    return cr_dt.strftime("%Y-%m-%dT%H:%M:%S")
# -------------------- Flask App --------------------
app = Flask(__name__)
CORS(app)  # habilita CORS para que el navegador pueda enviar POST

print("🌍 Usando URL pública de ngrok:", NGROK_URL)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

# -------------------- Endpoints --------------------
@app.route("/parent/login", methods=["GET", "POST"])
def parent_login():
    if request.method == "GET":
        return render_template("parent_login.html")
    
    email = request.form.get("email")
    password = request.form.get("password")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT email, name FROM parents WHERE email = %s AND password = %s", (email, password))
    parent = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if parent:
        session["parent_email"] = parent["email"]
        return redirect(url_for("parent_map"))  # redirects to /parent/map
    else:
        return render_template("parent_login.html", error="Invalid email or password")

@app.route("/parent/map")
def parent_map():
    if "parent_email" not in session:
        return redirect(url_for("parent_login"))

    parent_email = session["parent_email"]

    # 1️⃣ Obtener todos los hijos del padre
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT student_id, CONCAT(first_name, ' ', last_name) AS name
        FROM students
        WHERE parent_email = %s
    """, (parent_email,))
    children = cursor.fetchall()
    cursor.close()
    conn.close()

    if not children:
        return "<h3>No student linked to this parent.</h3>", 404

    parent_child_ids = [c["student_id"] for c in children]

    # 2️⃣ Inicializar mapa
    default_coords = (10.05, -85.42)  # Hojancha
    m = folium.Map(location=default_coords, zoom_start=15)
    dropoff_cluster = MarkerCluster(name="Drop-offs").add_to(m)

    # --- Variables para markers ---
    all_boarded_students = []      # lista global de estudiantes a bordo
    board_marker_coords = None
    parent_boarded_coords = None
    boarding_anon_counter = 1
    dropoff_anon_counter = 1

    # 3️⃣ Recorrer los hijos del padre
    for child in children:
        child_id = child["student_id"]

        # Último viaje del hijo
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.trip_id
            FROM trips t
            JOIN trip_students ts ON t.trip_id = ts.trip_id
            WHERE ts.student_id = %s
            ORDER BY t.trip_id DESC
            LIMIT 1
        """, (child_id,))
        trip = cursor.fetchone()
        cursor.close()
        conn.close()

        if not trip:
            continue

        trip_id = trip["trip_id"]
        students = get_students_by_trip(trip_id)

        # 4️⃣ Agregar estudiantes a la lista global de boarding
        for s in students:
            # Si el estudiante ya fue agregado, omitir
            if s["student_id"] in [st["id"] for st in all_boarded_students]:
                continue

            # Si es hijo del padre → mostrar nombre real
            if s["student_id"] in parent_child_ids:
                display_name = s["name"]
            else:
                display_name = f"Student #{boarding_anon_counter}"
                boarding_anon_counter += 1

            all_boarded_students.append({
                "id": s["student_id"],
                "name": display_name,
                "real_name": s["name"]
            })

            # Coordenadas del marker global azul
            if not board_marker_coords and s.get("boarded_lat") and s.get("boarded_lng"):
                board_marker_coords = (s["boarded_lat"], s["boarded_lng"])

            # Coordenadas para centrar en el hijo
            if s["student_id"] in parent_child_ids and not parent_boarded_coords:
                parent_boarded_coords = (s["boarded_lat"], s["boarded_lng"])

        # 5️⃣ Crear drop-off markers
        for s in students:
            if s.get("dropoff_lat") and s.get("dropoff_lng"):
                if s["student_id"] in parent_child_ids:
                    # Drop-off del hijo → azul con casita blanca
                    display_name = s["name"]
                    popup_html = f"""
                    <div style="font-family: Arial, sans-serif; font-size: 14px;">
                        <b>🏠 Drop-off</b><br>
                        <b>Student:</b> {display_name}<br>
                        <b>Time:</b> {s.get('dropoff_time') or 'Unknown'}
                    </div>
                    """
                    folium.Marker(
                        [s["dropoff_lat"], s["dropoff_lng"]],
                        popup=folium.Popup(popup_html, max_width=250),
                        icon=folium.Icon(color="blue", icon="home", prefix="fa")
                    ).add_to(dropoff_cluster)
                else:
                    # Drop-off anónimo → verde con casita blanca
                    display_name = f"Student #{dropoff_anon_counter}"
                    dropoff_anon_counter += 1
                    popup_html = f"""
                    <div style="font-family: Arial, sans-serif; font-size: 14px;">
                        <b>🏠 Drop-off</b><br>
                        <b>Student:</b> {display_name}<br>
                        <b>Time:</b> {s.get('dropoff_time') or 'Unknown'}
                    </div>
                    """
                    folium.Marker(
                        [s["dropoff_lat"], s["dropoff_lng"]],
                        popup=folium.Popup(popup_html, max_width=250),
                        icon=folium.Icon(color="green", icon="home", prefix="fa")
                    ).add_to(dropoff_cluster)

    # 6️⃣ Marker global azul (lista de todos los estudiantes)
    if all_boarded_students and board_marker_coords:
        names_list = "".join(f"<li>{s['name']}</li>" for s in all_boarded_students)
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 14px;">
            <b>🚌 All Boarding Students:</b><br>
            <ul style="margin:5px 0 0 15px; padding:0;">
                {names_list}
            </ul>
        </div>
        """
        folium.Marker(
            location=board_marker_coords,
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color="blue", icon="school")
        ).add_to(m)

    # 7️⃣ Centrar mapa según el hijo o boarding marker
    if parent_boarded_coords:
        m.location = parent_boarded_coords
    elif board_marker_coords:
        m.location = board_marker_coords

    return m._repr_html_()

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
    student.boarded_time_mysql = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    student.boarded_time = to_cr_time_str(data.get("timestamp") or datetime.utcnow().isoformat())
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
    
    if not app_state.pre_scanned_students:
        return jsonify({"status": "error", "message": "There are no students on board, cannot start the trip"}), 400

    # To improve in the future: integrate plate and school_phone
    current_plate = "BUS123"
    school_phone = "26599085"

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # insert trip
        cursor.execute("""
            INSERT INTO trips (plate, school_phone, trip_date, departure_time)
            VALUES (%s, %s, CURDATE(), CURTIME())
        """, (current_plate, school_phone))
        conn.commit()
        current_trip_id = cursor.lastrowid
        app_state.current_trip_id = current_trip_id

        # Create Bus object and add scanned students
        bus = Bus(current_plate)

        for s in app_state.pre_scanned_students:

            # Insert in trip_students (with boarded_time in MySQL format)
            cursor.execute("""
                INSERT INTO trip_students (
                    trip_id, student_id, status, boarded_time, boarded_lat, boarded_lng
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (app_state.current_trip_id, s.student_id, s.status, s.boarded_time, s.boarded_lat, s.boarded_lng))
            bus.board_student(s)    # board student object to bus object
            # ---set initial location using first pre scanned student ---
            if s == app_state.pre_scanned_students[0] and s.boarded_lat and s.boarded_lng:
                init_loc = BusLocation(
                    lat=float(s.boarded_lat),
                    lng=float(s.boarded_lng),
                    timestamp=s.boarded_time,  # hora del escaneo
                    plate=bus.plate
                )
                bus.locations.append(init_loc)
        conn.commit()
        print(f"🚍 Viaje iniciado con {len(bus.students_onboard)} estudiantes (trip_id={app_state.current_trip_id})")

    except Exception as e:
        conn.rollback()
        print("Error al iniciar viaje:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()

    # clean memory
    app_state.current_bus = bus
    app_state.bus_tracker.coords_by_bus.setdefault(current_plate, [])
    start_new_trip(plate=current_plate)
    app_state.trip_in_progress = True    # update trip status
    app_state.pre_scanned_students = []  # clean pre scanned memory at the start trip

    return jsonify({"status": "ok", "trip_id": app_state.current_trip_id, "message": "Viaje iniciado"})

@app.route("/alight_student", methods=["POST"])
def alight_student():
    """Mark student as dropped_off (DB)"""
    data = request.get_json()
    student_id = data.get("student_id")
    lat = data.get("lat")
    lng = data.get("lng")

    if not student_id:
        return jsonify({"status": "error", "message": "student_id not founded"}), 400

    if not app_state.trip_in_progress or not app_state.current_trip_id:
        return jsonify({
            "status": "error",
            "message": "The trip did not start yet. Students cannot be dropped off now."
        }), 400

    # Update DB
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

    # --- Update local state ---
    if app_state.current_bus:
        now = datetime.now()

        # 1. Update student in memory
        for s in app_state.current_bus.students_onboard:
            if str(s.student_id) == str(student_id):
                s.status = "dropped_off"
                s.dropoff_time = now.strftime("%Y-%m-%d %H:%M:%S")
                s.dropoff_lat = lat
                s.dropoff_lng = lng
                break

        # timestamp from frontend
        ts_str = data.get("timestamp")
        local_ts_str = to_cr_time_str(ts_str)

        # guardar en memoria
        app_state.current_bus.locations.append(
            BusLocation(
                lat=float(lat),
                lng=float(lng),
                timestamp=local_ts_str,
                plate=app_state.current_bus.plate
            )
        )

    return jsonify({"status": "ok", "message": "Student dropped off"}), 200

@app.route("/get_boarded_students", methods=["GET"])
def get_boarded_students():
    '''get boarded students: if there is trip_id -> from DB; if not -> pre-scanned memory'''
    if app_state.current_trip_id: # If trip exists look into the Data Base
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
        # If trip does not exists yet, return pre-scanned memory
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
    """stops trip if there are no students onbard; updates DB and save JSON"""
    if not app_state.trip_in_progress or not app_state.current_trip_id:
        return jsonify({"status": "error", "message": "No current trip"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # check if there are students onboard
    cursor.execute("""
        SELECT COUNT(*) AS onboard_count
        FROM trip_students
        WHERE trip_id = %s AND status = 'onboard'
    """, (app_state.current_trip_id,))
    onboard_count = cursor.fetchone()["onboard_count"]

    if onboard_count > 0:
        cursor.close()
        conn.close()
        return jsonify({"status": "error", "message": "There are students onboard. The trip cannot be stopped"}), 400

    # save arrival time before stop trip
    cursor.execute("""
        UPDATE trips
        SET arrival_time = CURTIME()
        WHERE trip_id = %s
    """, (app_state.current_trip_id,))
    conn.commit()
    cursor.close()
    conn.close()

    # stop trip without students on board.
    app_state.trip_in_progress = False
    # save JSON with current trip information
    save_current_trip()

    # restore app state flags
    app_state.trip_in_progress = False
    app_state.current_trip_id = None
    app_state.current_bus = None
    app_state.current_trip_file = None

    return jsonify({"status": "ok", "message": "Trip stopped."}), 200

@app.route("/location", methods=["POST"])
def location():
    """add coords to current trip with local Costa Rica time"""
    if not app_state.trip_in_progress or not app_state.current_bus:
        return jsonify({"status": "error", "message": "No current trip"}), 400

    data = request.get_json()
    required_keys = {"lat", "lng", "timestamp"}
    if not data or not required_keys.issubset(data.keys()):
        print("📱 Missing data:", data)
        return jsonify({"status": "error", "message": "Missing data"}), 400

    lat = data["lat"]
    lng = data["lng"]
    timestamp = data["timestamp"]

    # --- timestamp UTC to Costa Rica timezone ---
    local_ts_str = to_cr_time_str(timestamp)

    # add locations to bus and BusTracker
    app_state.current_bus.add_location(lat, lng, local_ts_str)
    app_state.bus_tracker.add_location(app_state.current_bus.plate, lat, lng, local_ts_str)

    print(f"Latitude: {lat} Longitude: {lng} Time: {timestamp} (plate={app_state.current_bus.plate})")
    return jsonify({
                "status": "ok",
                "plate": app_state.current_bus.plate,
                "lat": lat,
                "lng": lng,
                "timestamp": timestamp
            }), 200

@app.route("/map")
def show_map():
    """HTML map with the trip route and drop marks (using folium and app_state)"""

    # --- 1️⃣ Preparar bus temporal si no hay current_bus pero hay pre-scanned students ---
    if not app_state.current_bus and app_state.pre_scanned_students:
        temp_bus = Bus("BUS123")  # placa temporal
        for s in app_state.pre_scanned_students:
            temp_bus.board_student(s)
        bus = temp_bus
    else:
        bus = app_state.current_bus

    # --- 2️⃣ Determinar centro del mapa ---
    if bus and bus.locations:
        center = (bus.locations[-1].lat, bus.locations[-1].lng)
    elif bus:
        # Centrar en el primer estudiante con coordenadas
        first_student_with_coords = next(
            (s for s in bus.students_onboard if s.boarded_lat is not None and s.boarded_lng is not None),
            None
        )
        if first_student_with_coords:
            center = (first_student_with_coords.boarded_lat, first_student_with_coords.boarded_lng)
        else:
            center = (10.05, -85.42)  # default Hojancha
    else:
        center = (10.05, -85.42)  # default Hojancha

    m = folium.Map(location=center, zoom_start=15)

    # Draw route
    if app_state.current_bus and len(app_state.current_bus.locations) > 1:
        path = [(c.lat, c.lng) for c in app_state.current_bus.locations]
        folium.PolyLine(path, color="blue", weight=5).add_to(m)

        # --- BOARDING MARKER ---
        boarded_students = [s for s in app_state.current_bus.students_onboard if s.boarded_lat is not None]
        if boarded_students:
            # Create HTML list of names
            names_list = "".join(f"<li>{s.name}</li>" for s in boarded_students)
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 14px;">
                <b>🚌 Boarding Students:</b><br>
                <ul style="margin:5px 0 0 15px; padding:0;">
                    {names_list}
                </ul>
            </div>
            """
            # Use first boarded student's location to set boarded point in school
            first = boarded_students[0]
            folium.Marker(
                location=[first.boarded_lat, first.boarded_lng],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color="blue", icon="school")
            ).add_to(m)

        # --- DROP-OFF MARKERS with clustering  ---
        dropoff_cluster = MarkerCluster(name="Drop-offs").add_to(m)
        for s in app_state.current_bus.students_onboard:
            if s.status == "dropped_off" and s.dropoff_lat is not None and s.dropoff_lng is not None:
                dropoff_time = s.dropoff_time or "Unknown"
                popup_html = f"""
                <div style="font-family: Arial, sans-serif; font-size: 14px;">
                    <b>🏠 Drop-off</b><br>
                    <b>Student:</b> {s.name}<br>
                    <b>Time:</b> {dropoff_time}
                </div>
                """
                folium.Marker(
                    location=(s.dropoff_lat, s.dropoff_lng),
                    popup=folium.Popup(popup_html, max_width=250),
                    icon=folium.Icon(color="green", icon="home")
                ).add_to(dropoff_cluster)

    return m._repr_html_()

# -------------------- Run Flask --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)