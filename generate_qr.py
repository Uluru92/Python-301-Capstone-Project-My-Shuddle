import qrcode

# Random students data for test
student = {
    "student_id": 1,
    "name": "Juan Perez",
    "grade": "5A",
    "bus_id": 2
}

# Convertir los datos a un string (puede ser JSON)
import json
student_data = json.dumps(student)

# Crear QR
qr = qrcode.QRCode(
    version=1,
    box_size=10,
    border=4
)
qr.add_data(student_data)
qr.make(fit=True)

# Generar imagen
img = qr.make_image(fill_color="black", back_color="white")
img.save(f"student_{student['student_id']}.png")
