from tkinter import *
from tkinter import ttk
from tkcalendar import DateEntry
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

    # Inputs for parent registration:
    ttk.Label(student_window, text="Parent email:").grid(column=0, row=0, sticky=W)
    entry_parent_email = ttk.Entry(student_window, width=25)
    entry_parent_email.grid(column=1, row=0)

    ttk.Label(student_window, text="Name:").grid(column=0, row=1, sticky=W)
    entry_student_name = ttk.Entry(student_window, width=25)
    entry_student_name.grid(column=1, row=1)

    ttk.Label(student_window, text="Last Name:").grid(column=0, row=2, sticky=W)
    entry_student_last_name = ttk.Entry(student_window, width=25)
    entry_student_last_name.grid(column=1, row=2)
    
    selected_date_var = StringVar(value="No date selected")
    
    def select_birth_date():
        birthday_window = Toplevel(root)
        birthday_window.title("Select Birth Date")
        birthday_window.geometry("400x300")

        ttk.Label(birthday_window, text="Select Birth Date:").pack(pady=10)

        birth_date = DateEntry(birthday_window, width=15, background="darkblue",
                       foreground="white", borderwidth=2,
                       date_pattern="yyyy-mm-dd")  # format for MySQL
        birth_date.pack(pady=10)

        def save_date():
            selected = birth_date.get()  # returns string "YYYY-MM-DD"
            selected_date_var.set(selected)  # update label text
            birthday_window.destroy()

        ttk.Button(birthday_window, text="Save date", command=save_date).pack(pady=10)

    ttk.Button(student_window, text="Select Birth Date", command=select_birth_date).grid(column=0, row=3, sticky=W)
    ttk.Label(student_window, textvariable=selected_date_var).grid(column=1, row=3, sticky=W)

    def save_student_info():
        # Clean information
        parent_email = entry_parent_email.get().strip()
        name = entry_student_name.get().strip()
        last_name = entry_student_last_name.get().strip()
        birth_day = selected_date_var.get().strip()


        if not parent_email or not name or not last_name or not birth_day :
            messagebox.showerror("Error", "All fields are required.")
            return

        conn = connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT email FROM parents WHERE email = %s", (parent_email,))
            parent = cursor.fetchone()

            if not parent:
                messagebox.showerror("Error", "Parent email not found. Please register the parent first.")
                return
                
            cursor.execute("""
                INSERT INTO students (parent_email, first_name, last_name, birth_date)
                VALUES (%s, %s, %s, %s)
                """, (parent_email, name, last_name, birth_day))

            conn.commit()
            messagebox.showinfo("Success", f"Student {name} registered successfully!")

            # Clear fields after success
            entry_parent_email.delete(0, END)
            entry_student_name.delete(0, END)
            entry_student_last_name.delete(0, END)
            selected_date_var.set("No date selected")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    # Call to registration:
    ttk.Button(student_window, text="Register", width=25, command=save_student_info).grid(column=1, row=4, sticky=W)
    # Call to exit:
    ttk.Button(student_window, text="Logout", width=25, command=student_window.destroy).grid(column=1, row=5, sticky=W)

# Register Bus
def register_bus():
    bus_window  = Toplevel(root)
    bus_window .title("Bus Registration")
    bus_window .geometry("400x300")

    # Inputs for buses registration:
    ttk.Label(bus_window, text="Plate:").grid(column=0, row=0, sticky=W)
    entry_bus_plate = ttk.Entry(bus_window, width=25)
    entry_bus_plate.grid(column=1, row=0)

    ttk.Label(bus_window, text="Driver Name:").grid(column=0, row=1, sticky=W)
    entry_driver_name = ttk.Entry(bus_window, width=25)
    entry_driver_name.grid(column=1, row=1)

    ttk.Label(bus_window, text="Driver Phone:").grid(column=0, row=2, sticky=W)
    entry_driver_phone = ttk.Entry(bus_window, width=25)
    entry_driver_phone.grid(column=1, row=2)

    ttk.Label(bus_window, text="Attendant Name:").grid(column=0, row=3, sticky=W)
    entry_attendant_name = ttk.Entry(bus_window, width=25)
    entry_attendant_name.grid(column=1, row=3)

    ttk.Label(bus_window, text="Attendant Phone:").grid(column=0, row=4, sticky=W)
    entry_attendant_phone = ttk.Entry(bus_window, width=25)
    entry_attendant_phone.grid(column=1, row=4)

    def save_bus_info():
        # Clean information
        plate = entry_bus_plate.get().strip()
        driver_name = entry_driver_name.get().strip()
        driver_phone = entry_driver_phone.get().strip()
        attendant_name = entry_attendant_name.get().strip()
        attendant_phone = entry_attendant_phone.get().strip()

        if not plate or not driver_name or not driver_phone or not attendant_name or not attendant_phone:
            messagebox.showerror("Error", "All fields are required.")
            return

        conn = connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO buses (plate, driver_name, driver_phone, attendant_name, attendant_phone)
                VALUES (%s, %s, %s, %s, %s)
                """, (plate, driver_name, driver_phone, attendant_name, attendant_phone))

            conn.commit()
            messagebox.showinfo("Success", f"Bus {plate} registered successfully!")

            # Clear fields after success
            entry_bus_plate.delete(0, END)
            entry_driver_name.delete(0, END)
            entry_driver_phone.delete(0, END)
            entry_attendant_name.delete(0, END)
            entry_attendant_phone.delete(0, END)

        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", f"Bus {plate} already exists.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    ttk.Button(bus_window, text="Register", width=25, command=save_bus_info).grid(column=1, row=5, sticky=W)
    ttk.Button(bus_window, text="Logout", width=25, command=bus_window.destroy).grid(column=1, row=6, sticky=W)

# View trips
def view_trips():
    pass

# Create window tkinter
def main():
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

main()
