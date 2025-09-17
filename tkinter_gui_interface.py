from tkinter import *
from tkinter import ttk
from tkcalendar import DateEntry
from tkinter import messagebox
from PIL import Image, ImageTk
import mysql.connector, qrcode, json, os
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
def open_admin_dashboard(root):
    root.withdraw()
    dashboard_window = Toplevel(root)
    dashboard_window.title("Admin Dashboard - MyShuddle")
    dashboard_window.geometry("400x300")

    Label(dashboard_window, text="MyShuddle Admin Panel", font=("Arial", 14, "bold")).pack(pady=10)
    Button(dashboard_window, text="Register School", width=20, command=lambda:register_school(dashboard_window)).pack(pady=5)
    Button(dashboard_window, text="Register Parent", width=20, command=lambda:register_parent(dashboard_window)).pack(pady=5)
    Button(dashboard_window, text="Register Student", width=20, command=lambda: register_student(dashboard_window)).pack(pady=5)
    Button(dashboard_window, text="Register Bus", width=20, command=lambda: register_bus(dashboard_window)).pack(pady=5)
    Button(dashboard_window, text="View Trips", width=20, command=view_trips).pack(pady=5)
    Button(dashboard_window, text="Logout", width=20, command=lambda: on_close_dashboard(dashboard_window,root)).pack(pady=20)
    
    def on_close_dashboard(window, root):
        window.destroy()
        root.deiconify()

    dashboard_window.protocol("WM_DELETE_WINDOW", lambda: on_close_dashboard(dashboard_window, root))
    root.wait_window(dashboard_window)

# Login function
def login(root, entry_user, entry_pass):
    email = entry_user.get()
    password = entry_pass.get()

    if email == admin_email and password == admin_password:
        messagebox.showinfo("Login Success", f"Welcome, {email}!")
        open_admin_dashboard(root)
    else:
        messagebox.showerror("Login Failed", "Invalid admin credentials.")

# Register School
def register_school(parent_window):
    parent_window.withdraw()
    school_window = Toplevel(parent_window)
    school_window.title("School Registration")
    school_window.geometry("400x300")

    # Inputs for parent registration:
    ttk.Label(school_window, text="Phone Number:").grid(column=0, row=0, sticky=W)
    entry_school_phone= ttk.Entry(school_window, width=25)
    entry_school_phone.grid(column=1, row=0)

    ttk.Label(school_window, text="School Name:").grid(column=0, row=1, sticky=W)
    entry_school_name = ttk.Entry(school_window, width=25)
    entry_school_name.grid(column=1, row=1)

    ttk.Label(school_window, text="Address:").grid(column=0, row=2, sticky=W)
    entry_school_address = ttk.Entry(school_window, width=25)
    entry_school_address.grid(column=1, row=2)

    def save_school_info():
        # Clean information
        school_phone = entry_school_phone.get().strip()
        school_name = entry_school_name.get().strip()
        school_address = entry_school_address.get().strip()

        if not school_phone or not school_name or not school_address:
            messagebox.showerror("Error", "All fields are required.")
            return

        conn = connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO schools (school_phone, school_name, school_address)
                VALUES (%s, %s, %s)
                """, (school_phone, school_name, school_address))

            conn.commit()
            messagebox.showinfo("Success", f"Parent {school_name} registered successfully!")

            # Clear fields after success
            entry_school_name.delete(0, END)
            entry_school_address.delete(0, END)
            entry_school_phone.delete(0, END)

        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", f"School {school_name} already exists.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    # Call to registration:
    ttk.Button(school_window, text="Register", width=25, command=save_school_info).grid(column=1, row=5, sticky=W)

    # Call to exit:
    def close_school_window(window, parent_window):
        window.destroy()
        parent_window.deiconify() 
    
    ttk.Button(school_window, text="Logout", width=25, command=lambda:close_school_window(school_window, parent_window)).grid(column=1, row=6, sticky=W)

    school_window.protocol("WM_DELETE_WINDOW", lambda:close_school_window(school_window, parent_window))
    school_window.grab_set()
    school_window.focus_force()
    school_window.wait_window()

# Register Parent
def register_parent(parent_window):
    parent_window.withdraw()
    parents_window = Toplevel(parent_window)
    parents_window.title("Parent Registration")
    parents_window.geometry("400x300")

    # Inputs for parent registration:
    ttk.Label(parents_window, text="Email:").grid(column=0, row=0, sticky=W)
    entry_email = ttk.Entry(parents_window, width=25)
    entry_email.grid(column=1, row=0)

    ttk.Label(parents_window, text="Password:").grid(column=0, row=1, sticky=W)
    entry_password = ttk.Entry(parents_window, width=25, show="*")
    entry_password.grid(column=1, row=1)

    ttk.Label(parents_window, text="Name:").grid(column=0, row=2, sticky=W)
    entry_name = ttk.Entry(parents_window, width=25)
    entry_name.grid(column=1, row=2)

    ttk.Label(parents_window, text="Last Name:").grid(column=0, row=3, sticky=W)
    entry_last_name = ttk.Entry(parents_window, width=25)
    entry_last_name.grid(column=1, row=3)

    ttk.Label(parents_window, text="Phone:").grid(column=0, row=4, sticky=W)
    entry_phone = ttk.Entry(parents_window, width=25)
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
    ttk.Button(parents_window, text="Register", width=25, command=save_parent_info).grid(column=1, row=5, sticky=W)

    # Call to exit:
    def close_parents_window(window, parent_window):
        window.destroy()
        parent_window.deiconify() 
    
    ttk.Button(parents_window, text="Logout", width=25, command=lambda:close_parents_window(parents_window, parent_window)).grid(column=1, row=6, sticky=W)

    parents_window.protocol("WM_DELETE_WINDOW", lambda:close_parents_window(parents_window, parent_window))
    parents_window.grab_set()
    parents_window.focus_force()
    parents_window.wait_window()

# Register Student
def register_student(parent_window):
    parent_window.withdraw()
    student_window  = Toplevel(parent_window)
    student_window .title("Student Registration")
    student_window .geometry("600x600")

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
    
    # --- School selection (ComboBox) ---
    ttk.Label(student_window, text="School:").grid(column=0, row=3, sticky=W)
    school_var = StringVar()
    combo_school = ttk.Combobox(student_window, textvariable=school_var, width=25, state="readonly")
    combo_school.grid(column=1, row=3)

    # Load schools from DB
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT school_id, name FROM schools")
    schools = cursor.fetchall()
    conn.close()

    school_map = {name: school_id for school_id, name in schools}  # map name -> id
    combo_school['values'] = list(school_map.keys())
    if combo_school['values']:
        combo_school.current(0)  # select default 0

    # --- Birthday selection Modal ---
    selected_date_var = StringVar(value="No date selected")
    
    def select_birth_date():
        birthday_window = Toplevel(student_window)
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
        birthday_window.transient(student_window)  
        birthday_window.grab_set()  
        
    ttk.Button(student_window, text="Select Birth Date", command=select_birth_date).grid(column=0, row=4, sticky=W)
    ttk.Label(student_window, textvariable=selected_date_var).grid(column=1, row=4, sticky=W)

    def save_student_info():
        # Clean information
        parent_email = entry_parent_email.get().strip()
        name = entry_student_name.get().strip()
        last_name = entry_student_last_name.get().strip()
        birth_day = selected_date_var.get().strip()
        school_name = school_var.get().strip()

        if not parent_email or not name or not last_name or not birth_day or not school_name:
            messagebox.showerror("Error", "All fields are required.")
            return
        
        school_id = school_map.get(school_name)  # get ID from school

        conn = connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT email FROM parents WHERE email = %s", (parent_email,))
            parent = cursor.fetchone()

            if not parent:
                messagebox.showerror("Error", "Parent email not found. Please register the parent first.")
                return
                
            cursor.execute("""
                INSERT INTO students (parent_email, first_name, last_name, birth_date, school_id)
                VALUES (%s, %s, %s, %s, %s)
                """, (parent_email, name, last_name, birth_day,school_id))

            conn.commit()

            student_id = cursor.lastrowid  # <<< ID student just created

            # Show QR created with the student info
            student = {
                "student_id": student_id,
                "name": f"{name} {last_name}",
                "parent_email": parent_email,
                "birth_date": birth_day
            }
            
            os.makedirs("qrs", exist_ok=True)

            student_data = json.dumps(student)
            qr = qrcode.QRCode(version=1, box_size=5, border=2)
            qr.add_data(student_data)
            qr.make(fit=True)

            file_path = f"qrs/student_{student_id}.png"
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(file_path)

            # Show QR generated
            qr_img = Image.open(file_path)
            qr_img = qr_img.resize((150, 150))
            tk_img = ImageTk.PhotoImage(qr_img)

            qr_label = Label(student_window, image=tk_img)
            qr_label.image = tk_img  # to keep reference
            qr_label.grid(column=1, row=5, pady=10)
            ttk.Label(student_window, text="--- Student QR ---").grid(column=1, row=6, sticky=EW)

            messagebox.showinfo("Success", f"Student {name} registered successfully!")

            # Clear fields after success
            entry_parent_email.delete(0, END)
            entry_student_name.delete(0, END)
            entry_student_last_name.delete(0, END)
            selected_date_var.set("No date selected")
            school_var.set("No school selected")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    # Call to registration:
    ttk.Button(student_window, text="Register", width=25, command=save_student_info).grid(column=1, row=7, sticky=W)

    # Call to exit:
    def close_student_window(window,parent_window):
        window.destroy()
        parent_window.deiconify() 
    
    ttk.Button(student_window, text="Logout", width=25, command=lambda:close_student_window(student_window, parent_window)).grid(column=1, row=8, sticky=W)

    student_window.protocol("WM_DELETE_WINDOW", lambda:close_student_window(student_window, parent_window))
    student_window.grab_set()
    student_window.focus_force()
    student_window.wait_window()

# Register Bus
def register_bus(parent_window):
    parent_window.withdraw()
    bus_window  = Toplevel(parent_window)
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

    # Call to exit:
    def close_student_window(window,parent_window):
        window.destroy()
        parent_window.deiconify() 
    
    ttk.Button(bus_window, text="Logout", width=25, command=lambda:close_student_window(bus_window, parent_window)).grid(column=1, row=6, sticky=W)

    bus_window.protocol("WM_DELETE_WINDOW", lambda:close_student_window(bus_window, parent_window))
    bus_window.grab_set()
    bus_window.focus_force()
    bus_window.wait_window()

# View trips
def view_trips():
    pass

# Create window tkinter
def run_main():
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

    ttk.Button(frm, text="Login", command=lambda: login(root, entry_user, entry_pass)).grid(column=1, row=2, pady=5)
    ttk.Button(frm, text="Logout", command=root.destroy).grid(column=1, row=3)

    root.mainloop()

run_main()