from tkinter import *
from tkinter import ttk
import mysql.connector
from tkinter import messagebox
import os
from dotenv import load_dotenv

# Admin user Tkinter
admin_email = "admin@gmail.com"
admin_password = "admin123"

# Get passwords and secret stuff from .env
load_dotenv()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
DB_PORT = os.getenv("MYSQL_PORT")
MYSQL_DB_MYSHUDDLE = os.getenv("MYSQL_DB_MYSHUDDLE")

# Database connection
def connect_db():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,        
        password=MYSQL_PASSWORD,
        database=MYSQL_DB_MYSHUDDLE
    )

# Admin dashboard window
def open_admin_dashboard():
    dashboard = Toplevel(root)
    dashboard.title("Admin Dashboard - MyShuddle")
    dashboard.geometry("400x300")

    Label(dashboard, text="MyShuddle Admin Panel", font=("Arial", 14, "bold")).pack(pady=10)
    Button(dashboard, text="Register Parent", width=20, command=register_parent).pack(pady=5)
    Button(dashboard, text="Register Student", width=20, command=register_student).pack(pady=5)
    Button(dashboard, text="Register Bus", width=20, command=register_bus).pack(pady=5)
    Button(dashboard, text="View Trips", width=20, command=view_trips).pack(pady=5)
    Button(dashboard, text="Logout", width=20, command=dashboard.destroy).pack(pady=20)

# Login function
def login():
    email = entry_user.get()
    password = entry_pass.get()

    if email == admin_email and password == admin_password:
        messagebox.showinfo("Login Success", f"Welcome, {email}!")
        open_admin_dashboard()
    else:
        messagebox.showerror("Login Failed", "Invalid admin credentials.")

# Register Parent
def register_parent():
    parent_window  = Toplevel(root)
    parent_window .title("Parent Registration")
    parent_window .geometry("400x300")

    Button(parent_window, text="Logout", width=20, command=parent_window.destroy).pack(pady=20)
    pass

# Register Student
def register_student():
    student_window  = Toplevel(root)
    student_window .title("Student Registration")
    student_window .geometry("400x300")

    Button(student_window, text="Logout", width=20, command=student_window.destroy).pack(pady=20)
    pass

# Register Bus
def register_bus():
    bus_window  = Toplevel(root)
    bus_window .title("Bus Registration")
    bus_window .geometry("400x300")

    Button(bus_window, text="Logout", width=20, command=bus_window.destroy).pack(pady=20)
    pass

# View trips
def view_trips():

    pass

# Create window tkinter
root = Tk()
root.title("MyShuddle User Administrator")
root.geometry("300x200")

frm = ttk.Frame(root, padding=20)
frm.grid()

# Create inputs for log in
ttk.Label(frm, text="Email:").grid(column=0, row=0, sticky=W)
entry_user = ttk.Entry(frm, width=25)
entry_user.grid(column=1, row=0) 

ttk.Label(frm, text="Password:").grid(column=0, row=1, sticky=W)
entry_pass = ttk.Entry(frm, show="*", width=25)
entry_pass.grid(column=1, row=1)

ttk.Button(frm, text="Login", command=login).grid(column=1, row=2, pady=10)

root.mainloop()
