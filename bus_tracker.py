import tkinter as tk
from tkhtmlview import HTMLLabel
import folium
import io
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

# -------------------- Backend Flask --------------------
app = Flask(__name__)
CORS(app)  # habilita CORS para que el navegador pueda enviar POST
coords_list = []  # Lista de dicts: {'bus_id', 'lat', 'lng', 'timestamp'}

# URL pública de ngrok fija
PUBLIC_URL = "https://8e37d919c96a.ngrok-free.app"
print("🌍 Usando URL pública:", PUBLIC_URL)

@app.route("/")
def home():
    return open("index.html").read()

@app.route("/location", methods=["POST"])
def location():
    data = request.get_json()
    required_keys = {"bus_id", "lat", "lng", "timestamp"}
    if not data or not required_keys.issubset(data.keys()):
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    coords_list.append(data)
    print("Received:", data)
    return jsonify({"status": "ok"}), 200

def run_flask():
    app.run(host="0.0.0.0", port=5000, use_reloader=False)

# -------------------- Crear mapa --------------------
def create_map():
    if coords_list:
        center = (coords_list[-1]['lat'], coords_list[-1]['lng'])
    else:
        center = (10.05, -85.42)  # Hojancha

    m = folium.Map(location=center, zoom_start=15)

    # Dibujar ruta
    if len(coords_list) > 1:
        path = [(c['lat'], c['lng']) for c in coords_list]
        folium.PolyLine(path, color="blue", weight=5).add_to(m)

    # Agregar marcadores con info
    for i, c in enumerate(coords_list):
        popup_text = f"Bus: {c['bus_id']}<br>Lat: {c['lat']}<br>Lng: {c['lng']}<br>Hora: {c['timestamp']}"
        folium.Marker(location=(c['lat'], c['lng']), popup=popup_text).add_to(m)

    map_html = io.BytesIO()
    m.save(map_html, close_file=False)
    return map_html.getvalue().decode()

def update_map():
    html = create_map()
    map_label.set_html(html)
    root.after(5000, update_map)

# -------------------- Tkinter GUI --------------------
root = tk.Tk()
root.title("MyShuddle Bus Tracker")
root.geometry("800x600")

map_label = HTMLLabel(root, html="<h3>Loading map...</h3>")
map_label.pack(fill="both", expand=True)

root.after(1000, update_map)

# -------------------- Correr Flask --------------------
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

root.mainloop()
