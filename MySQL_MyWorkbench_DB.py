import mysql.connector
import os
from dotenv import load_dotenv

# Get passwords and secret stuff from .env
load_dotenv()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB_MYSHUDDLE = os.getenv("MYSQL_DB_MYSHUDDLE")


# Database connection
def connect_db():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,        
        password=MYSQL_PASSWORD,
        port=int(MYSQL_PORT) if MYSQL_PORT else 3306
    )

# Connect to MySQL
conn = connect_db() 
cursor = conn.cursor()

# Create Database
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB_MYSHUDDLE}")
conn.commit()
conn.close()

# Connect to MySQL -> MyShuddle Database
conn = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB_MYSHUDDLE,
    port=int(MYSQL_PORT) if MYSQL_PORT else 3306
)
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS parents (
    email VARCHAR(100) PRIMARY KEY,
    password VARCHAR(100),
    name VARCHAR(100),
    last_name VARCHAR(100),
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
print("✅ Connected to MyShuddle database successfully!")
print("✅ All tables created successfully!")