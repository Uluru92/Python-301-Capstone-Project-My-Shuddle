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
    parent_window = Toplevel(root)
    parent_window.title("Parent Registration")
    parent_window.geometry("400x300")

    # Inputs for parent registration:
    ttk.Label(parent_window, text="Email:").grid(column=0, row=0, sticky=W)
    entry_email = ttk.Entry(parent_window, width=25)
    entry_email.grid(column=1, row=0)

    ttk.Label(parent_window, text="Password:").grid(column=0, row=1, sticky=W)
    entry_password = ttk.Entry(parent_window, width=25, show="*")
    entry_password.grid(column=1, row=1)

    ttk.Label(parent_window, text="Name:").grid(column=0, row=2, sticky=W)
    entry_name = ttk.Entry(parent_window, width=25)
    entry_name.grid(column=1, row=2)

    ttk.Label(parent_window, text="Last Name:").grid(column=0, row=3, sticky=W)
    entry_last_name = ttk.Entry(parent_window, width=25)
    entry_last_name.grid(column=1, row=3)

    ttk.Label(parent_window, text="Phone:").grid(column=0, row=4, sticky=W)
    entry_phone = ttk.Entry(parent_window, width=25)
    entry_phone.grid(column=1, row=4)

    def save_parent_info():
        # Clean information
        email = entry_email.get().strip()
        password = entry_password.get().strip()
        name = entry_name.get().strip()
        last_name = entry_last_name.get().strip()
        phone = entry_phone.get().strip()

        if not email or not password or not name or not last_name or not phone:
            messagebox.showerror("Error", "All fields are required.")
            return

        conn = connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO parents (email, password, name, last_name, phone)
                VALUES (%s, %s, %s, %s, %s)
                """, (email, password, name, last_name, phone))

            conn.commit()
            messagebox.showinfo("Success", f"Parent {name} registered successfully!")

            # Clear fields after success
            entry_email.delete(0, END)
            entry_password.delete(0, END)
            entry_name.delete(0, END)
            entry_last_name.delete(0, END)
            entry_phone.delete(0, END)

        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", f"Email {email} already exists.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    # Call to registration:
    ttk.Button(parent_window, text="Register", width=20, command=save_parent_info).grid(column=1, row=5, sticky=W)
    # Call to exit:
    ttk.Button(parent_window, text="Logout", width=20, command=parent_window.destroy).grid(column=1, row=6, sticky=W)

# Register Student
def register_student():
    student_window  = Toplevel(root)
    student_window .title("Student Registration")
    student_window .geometry("400x300")

    '''
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    parent_email VARCHAR(100),
    name VARCHAR(100),
    grade VARCHAR(20),
    FOREIGN KEY (parent_email) REFERENCES parents(email)'''


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
