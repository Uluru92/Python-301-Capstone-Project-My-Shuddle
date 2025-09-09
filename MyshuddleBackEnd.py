from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # <-- allow cross-origin requests

@app.route("/location", methods=["POST"])
def location():
    data = request.get_json()
    print("Received data:", data)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(port=5000)
