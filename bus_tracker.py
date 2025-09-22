import os
import json
import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

# -------------------- Config --------------------
load_dotenv()
NGROK_URL = os.getenv("NGROK_URL")

# Variables globales
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
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MyShuddle Tracker</title>
    </head>
    <body>
        <h1>MyShuddle Tracker</h1>
        <button id="scanQRBtn">Scan Students QR</button>
        <button id="startBtn" disabled>Start Trip</button>
        <button id="stopBtn" disabled>Stop Trip</button>

        <script>
            const backendStartUrl = "{NGROK_URL}/start_trip";
            const backendLocationUrl = "{NGROK_URL}/location";
            const backendStopUrl = "{NGROK_URL}/stop_trip";

            let trackingInterval = null;

            // --- Scan QR ---
            document.getElementById("scanQRBtn").addEventListener("click", async () => {{
                alert("Aquí iría la lógica para escanear QR y registrar estudiantes.");
                // Después de escanear, habilitar el botón Start
                document.getElementById("startBtn").disabled = false;
            }});

            // --- Start Trip ---
            document.getElementById("startBtn").addEventListener("click", async () => {{
                try {{
                    const res = await fetch(backendStartUrl, {{ method: "POST" }});
                    const data = await res.json();
                    if (data.status !== "ok") throw new Error(data.message);

                    alert("Trip started!");
                    document.getElementById("startBtn").disabled = true;
                    document.getElementById("stopBtn").disabled = false;

                    const sendLocation = (pos) => {{
                        const locationData = {{
                            bus_id: "bus123",
                            lat: pos.coords.latitude,
                            lng: pos.coords.longitude,
                            timestamp: new Date().toISOString()
                        }};
                        fetch(backendLocationUrl, {{
                            method: "POST",
                            headers: {{ "Content-Type": "application/json" }},
                            body: JSON.stringify(locationData)
                        }}).then(res => res.json())
                          .then(r => console.log("Server response:", r))
                          .catch(err => console.error("Error sending location:", err));
                    }};

                    navigator.geolocation.getCurrentPosition(sendLocation);
                    trackingInterval = setInterval(() => {{
                        navigator.geolocation.getCurrentPosition(sendLocation);
                    }}, 30000);

                }} catch (err) {{
                    alert("Error starting trip: " + err.message);
                }}
            }});

            // --- Stop Trip ---
            document.getElementById("stopBtn").addEventListener("click", async () => {{
                try {{
                    const res = await fetch(backendStopUrl, {{ method: "POST" }});
                    const data = await res.json();
                    if (data.status !== "ok") throw new Error(data.message);

                    alert("Trip stopped!");
                    clearInterval(trackingInterval);
                    trackingInterval = null;

                    document.getElementById("startBtn").disabled = false;
                    document.getElementById("stopBtn").disabled = true;
                }} catch (err) {{
                    alert("Error stopping trip: " + err.message);
                }}
            }});
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

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
