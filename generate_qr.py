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

# Texto o ID para el QR
data = "Student ID: 1234 - Juan Perez"

# Crear QR
img = qrcode.make(data)

# Guardar como imagen
img.save("student_1234.png")

print("✅ QR generado: student_1234.png")