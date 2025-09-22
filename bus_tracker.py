import os
import json
import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# -------------------- Config --------------------
load_dotenv()
NGROK_URL = os.getenv("NGROK_URL")

# Variables globales to scan QRs and keep wich students are in board
boarded_students = []

# Variables globales to save every route after tracking bus
coords_list = []
current_trip_file = None
trip_in_progress = False


# -------------------- Helpers --------------------
def start_new_trip(bus_id="bus123"):
    """Inicia un nuevo viaje y crea un archivo JSON único"""
    global current_trip_file, coords_list, trip_in_progress
    coords_list = []
    os.makedirs("trips", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
        return jsonify({"status": "error", "message": "Datos de estudiante inválidos"}), 400

    # Verificar si ya está abordado
    if any(s['student_id'] == data['student_id'] for s in boarded_students):
        print(f"⚠️ {data['name']} ya estaba registrado")
        return (
            jsonify({
                "status": "ok",
                "student": data,
                "message": f"⚠️ {data['name']} ya estaba abordado"
            }),
            200,
            {"Cache-Control": "no-cache, no-store, must-revalidate"}
        )

    # Agregar nuevo estudiante
    boarded_students.append(data)
    print(f"🎓 {data['name']} boarded the bus")
    return (
        jsonify({
            "status": "ok",
            "student": data,
            "message": f"✅ {data['name']} abordó el bus"
        }),
        200,
        {"Cache-Control": "no-cache, no-store, must-revalidate"}
    )

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
    """Agrega coordenadas al viaje en curso"""
    global coords_list, trip_in_progress
    if not trip_in_progress:
        return jsonify({"status": "error", "message": "No hay viaje en curso"}), 400

    data = request.get_json()
    required_keys = {"bus_id", "lat", "lng", "timestamp"}
    if not data or not required_keys.issubset(data.keys()):
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    coords_list.append(data)
    save_current_trip()  # Guardar en JSON

    print(f"Latitude: {data['lat']} Longitude: {data['lng']}")
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
