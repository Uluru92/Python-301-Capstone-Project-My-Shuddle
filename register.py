import mysql.connector

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="yourpassword",
    database="myshuddle"
)
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS parents (
    email VARCHAR(100) PRIMARY KEY,
    name VARCHAR(100),
    phone VARCHAR(20)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    parent_email VARCHAR(100),
    name VARCHAR(100),
    grade VARCHAR(20),
    FOREIGN KEY (parent_email) REFERENCES parents(email)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS buses (
    bus_id INT AUTO_INCREMENT PRIMARY KEY,
    plate VARCHAR(20),
    capacity INT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS trips (
    trip_id INT AUTO_INCREMENT PRIMARY KEY,
    bus_id INT,
    trip_date DATE,
    FOREIGN KEY (bus_id) REFERENCES buses(bus_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS trip_students (
    trip_id INT,
    student_id INT,
    status ENUM('onboard', 'absent', 'dropped_off') DEFAULT 'onboard',
    PRIMARY KEY (trip_id, student_id),
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
)
""")

conn.commit()
conn.close()
print("✅ All tables created successfully!")