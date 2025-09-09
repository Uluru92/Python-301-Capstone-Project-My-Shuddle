from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Servir el index.html
@app.route("/")
def home_page():
    return send_from_directory('.', 'index.html')  # index.html en la misma carpeta que MyShuddleBackEnd.py

# Endpoint para recibir ubicación
@app.route("/location", methods=["POST"])
def location():
    data = request.get_json()
    print("Received data:", data)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    # Activar debug si querés ver cambios en tiempo real
    app.run(port=5000)
