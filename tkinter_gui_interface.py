from tkinter import *
from tkinter import ttk
from tkcalendar import DateEntry
from tkinter import messagebox
from PIL import Image, ImageTk
from pathlib import Path
import mysql.connector, qrcode, json, os, webbrowser, folium
from datetime import datetime
from dotenv import load_dotenv
from folium.plugins import MarkerCluster

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
    Button(dashboard_window, text="View Trips", width=20, command=lambda:view_trips(dashboard_window)).pack(pady=5)
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

    # Make a 2×2 grid on the root of this window
    school_window.grid_rowconfigure(0, weight=1)
    school_window.grid_rowconfigure(2, weight=1)
    school_window.grid_columnconfigure(0, weight=1)
    school_window.grid_columnconfigure(2, weight=1)

    # Center frame
    frm = ttk.Frame(school_window, padding=20)
    frm.grid(row=1, column=1, sticky="nsew")

    # Inputs for school registration:
    ttk.Label(frm, text="Phone Number:").grid(column=0, row=0, sticky=W, pady=5)
    entry_school_phone = ttk.Entry(frm, width=25)
    entry_school_phone.grid(column=1, row=0, pady=5)

    ttk.Label(frm, text="School Name:").grid(column=0, row=1, sticky=W, pady=5)
    entry_school_name = ttk.Entry(frm, width=25)
    entry_school_name.grid(column=1, row=1, pady=5)

    ttk.Label(frm, text="Address:").grid(column=0, row=2, sticky=W, pady=5)
    entry_school_address = ttk.Entry(frm, width=25)
    entry_school_address.grid(column=1, row=2, pady=5)

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
    ttk.Button(frm, text="Register", width=25, command=save_school_info).grid(column=1, row=5, sticky=W)

    # Call to exit:
    def close_school_window(window, parent_window):
        window.destroy()
        parent_window.deiconify() 
    
    ttk.Button(frm, text="Logout", width=25, command=lambda:close_school_window(school_window, parent_window)).grid(column=1, row=6, sticky=W)

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

    # Make a 2×2 grid on the root of this window
    parents_window.grid_rowconfigure(0, weight=1)
    parents_window.grid_rowconfigure(2, weight=1)
    parents_window.grid_columnconfigure(0, weight=1)
    parents_window.grid_columnconfigure(2, weight=1)

    # Center frame
    frm = ttk.Frame(parents_window, padding=20)
    frm.grid(row=1, column=1, sticky="nsew")

    # Inputs for parent registration:
    ttk.Label(frm, text="Email:").grid(column=0, row=0, sticky=W)
    entry_email = ttk.Entry(frm, width=25)
    entry_email.grid(column=1, row=0)

    ttk.Label(frm, text="Password:").grid(column=0, row=1, sticky=W)
    entry_password = ttk.Entry(frm, width=25, show="*")
    entry_password.grid(column=1, row=1)

    ttk.Label(frm, text="Name:").grid(column=0, row=2, sticky=W)
    entry_name = ttk.Entry(frm, width=25)
    entry_name.grid(column=1, row=2)

    ttk.Label(frm, text="Last Name:").grid(column=0, row=3, sticky=W)
    entry_last_name = ttk.Entry(frm, width=25)
    entry_last_name.grid(column=1, row=3)

    ttk.Label(frm, text="Phone:").grid(column=0, row=4, sticky=W)
    entry_phone = ttk.Entry(frm, width=25)
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
    ttk.Button(frm, text="Register", width=25, command=save_parent_info).grid(column=1, row=5, sticky=W)

    # Call to exit:
    def close_parents_window(window, parent_window):
        window.destroy()
        parent_window.deiconify() 
    
    ttk.Button(frm, text="Logout", width=25, command=lambda:close_parents_window(parents_window, parent_window)).grid(column=1, row=6, sticky=W)

    parents_window.protocol("WM_DELETE_WINDOW", lambda:close_parents_window(parents_window, parent_window))
    parents_window.grab_set()
    parents_window.focus_force()
    parents_window.wait_window()

# Register Student
def register_student(parent_window):
    parent_window.withdraw()
    student_window  = Toplevel(parent_window)
    student_window .title("Student Registration")
    student_window .geometry("500x600")

    # Make a 2×2 grid on the root of this window
    student_window.grid_rowconfigure(0, weight=1)
    student_window.grid_rowconfigure(2, weight=1)
    student_window.grid_columnconfigure(0, weight=1)
    student_window.grid_columnconfigure(2, weight=1)

    # Center frame
    frm = ttk.Frame(student_window, padding=10)
    frm.grid(row=1, column=1, sticky="nsew")

    # Make the window resizable
    frm.grid_rowconfigure(0, weight=1)
    frm.grid_columnconfigure(0, weight=1)

    # Create a scrollable frame
    canvas = Canvas(frm)
    scrollbar = Scrollbar(frm, orient="vertical", command=canvas.yview)
    scroll_frame = Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0,0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.grid(row=0, column=0, sticky="NSEW")
    scrollbar.grid(row=0, column=1, sticky="NS")

    # Inputs for parent registration:
    ttk.Label(scroll_frame, text="Parent email:").grid(column=0, row=0, sticky=W, pady=5)
    entry_parent_email = ttk.Entry(scroll_frame, width=30)
    entry_parent_email.grid(column=1, row=0, pady=5)

    ttk.Label(scroll_frame, text="First Name:").grid(column=0, row=1, sticky=W, pady=5)
    entry_student_name = ttk.Entry(scroll_frame, width=30)
    entry_student_name.grid(column=1, row=1, pady=5)

    ttk.Label(scroll_frame, text="Last Name:").grid(column=0, row=2, sticky=W, pady=5)
    entry_student_last_name = ttk.Entry(scroll_frame, width=30)
    entry_student_last_name.grid(column=1, row=2, pady=5)
    
     # --- School selection ---
    ttk.Label(scroll_frame, text="School:").grid(column=0, row=3, sticky=W, pady=5)
    school_var = StringVar()
    combo_school = ttk.Combobox(scroll_frame, textvariable=school_var, width=30, state="readonly")
    combo_school.grid(column=1, row=3, pady=5)

    # Load schools from DB
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT school_phone, school_name FROM schools")
    schools = cursor.fetchall()
    conn.close()

    # Map display_name -> school_phone
    school_map = {f"{phone} - {name}": phone for phone, name in schools}
    combo_school['values'] = list(school_map.keys())
    if combo_school['values']:
        combo_school.current(0)

    # --- Birthday selection ---
    selected_date_var = StringVar(value="No date selected")

    def select_birth_date():
        birthday_window = Toplevel(student_window)
        birthday_window.title("Select Birth Date")
        birthday_window.geometry("400x300")
        ttk.Label(birthday_window, text="Select Birth Date:").pack(pady=10)

        birth_date = DateEntry(birthday_window, width=15, background="darkblue",
                               foreground="white", borderwidth=2, date_pattern="yyyy-mm-dd")
        birth_date.pack(pady=10)

        def save_date():
            selected_date_var.set(birth_date.get())
            birthday_window.destroy()

        ttk.Button(birthday_window, text="Save date", command=save_date).pack(pady=10)
        birthday_window.transient(student_window)
        birthday_window.grab_set()

    ttk.Button(scroll_frame, text="Select Birth Date", command=select_birth_date).grid(column=0, row=4, sticky=W, pady=5)
    ttk.Label(scroll_frame, textvariable=selected_date_var).grid(column=1, row=4, sticky=W, pady=5)

    # --- Save student info ---
    def save_student_info():
        parent_email = entry_parent_email.get().strip()
        first_name = entry_student_name.get().strip()
        last_name = entry_student_last_name.get().strip()
        birth_day = selected_date_var.get().strip()
        school_selection = school_var.get()
        school_phone = school_map.get(school_selection)

        if not parent_email or not first_name or not last_name or not birth_day or not school_phone:
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
                INSERT INTO students (parent_email, first_name, last_name, birth_date, school_phone)
                VALUES (%s, %s, %s, %s, %s)
            """, (parent_email, first_name, last_name, birth_day, school_phone))
            conn.commit()
            student_id = cursor.lastrowid

            # Generate QR
            student_data = json.dumps({
                "student_id": student_id,
                "name": f"{first_name} {last_name}",
                "parent_email": parent_email,
                "birth_date": birth_day,
                "school_phone": school_phone
            })
            os.makedirs("qrs", exist_ok=True)
            qr_file = f"qrs/student_{student_id}.png"
            qr = qrcode.make(student_data)
            qr.save(qr_file)

            # Show QR
            qr_img = Image.open(qr_file).resize((150, 150))
            tk_img = ImageTk.PhotoImage(qr_img)
            qr_label = Label(scroll_frame, image=tk_img)
            qr_label.image = tk_img
            qr_label.grid(column=1, row=5, pady=10)
            ttk.Label(scroll_frame, text="--- Student QR ---").grid(column=1, row=6, pady=5)

            messagebox.showinfo("Success", f"Student {first_name} registered successfully!")
            # Clear fields
            entry_parent_email.delete(0, END)
            entry_student_name.delete(0, END)
            entry_student_last_name.delete(0, END)
            selected_date_var.set("No date selected")
            school_var.set(combo_school['values'][0])

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    ttk.Button(scroll_frame, text="Register", width=30, command=save_student_info).grid(column=1, row=7, sticky=W, pady=5)

    # --- Logout button ---
    def close_student_window(window, parent_window):
        window.destroy()
        parent_window.deiconify()

    ttk.Button(scroll_frame, text="Logout", width=30, command=lambda: close_student_window(student_window, parent_window)).grid(column=1, row=8, sticky=W, pady=5)

    student_window.protocol("WM_DELETE_WINDOW", lambda: close_student_window(student_window, parent_window))
    student_window.grab_set()
    student_window.focus_force()
    student_window.wait_window()

# Register Bus
def register_bus(parent_window):
    parent_window.withdraw()
    bus_window  = Toplevel(parent_window)
    bus_window .title("Bus Registration")
    bus_window .geometry("400x300")

    # Make a 2×2 grid on the root of this window
    bus_window.grid_rowconfigure(0, weight=1)
    bus_window.grid_rowconfigure(2, weight=1)
    bus_window.grid_columnconfigure(0, weight=1)
    bus_window.grid_columnconfigure(2, weight=1)

    # Center frame
    frm = ttk.Frame(bus_window, padding=20)
    frm.grid(row=1, column=1, sticky="nsew")

    # Inputs for buses registration:
    ttk.Label(frm, text="Plate:").grid(column=0, row=0, sticky=W)
    entry_bus_plate = ttk.Entry(frm, width=25)
    entry_bus_plate.grid(column=1, row=0)

    ttk.Label(frm, text="Driver Name:").grid(column=0, row=1, sticky=W)
    entry_driver_name = ttk.Entry(frm, width=25)
    entry_driver_name.grid(column=1, row=1)

    ttk.Label(frm, text="Driver Phone:").grid(column=0, row=2, sticky=W)
    entry_driver_phone = ttk.Entry(frm, width=25)
    entry_driver_phone.grid(column=1, row=2)

    ttk.Label(frm, text="Attendant Name:").grid(column=0, row=3, sticky=W)
    entry_attendant_name = ttk.Entry(frm, width=25)
    entry_attendant_name.grid(column=1, row=3)

    ttk.Label(frm, text="Attendant Phone:").grid(column=0, row=4, sticky=W)
    entry_attendant_phone = ttk.Entry(frm, width=25)
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

    ttk.Button(frm, text="Register", width=25, command=save_bus_info).grid(column=1, row=5, sticky=W)

    # Call to exit:
    def close_student_window(window,parent_window):
        window.destroy()
        parent_window.deiconify() 
    
    ttk.Button(frm, text="Logout", width=25, command=lambda:close_student_window(bus_window, parent_window)).grid(column=1, row=6, sticky=W)

    bus_window.protocol("WM_DELETE_WINDOW", lambda:close_student_window(bus_window, parent_window))
    bus_window.grab_set()
    bus_window.focus_force()
    bus_window.wait_window()

# View trips
def view_trips(parent_window):
    parent_window.withdraw()
    trips_window = Toplevel(parent_window)
    trips_window.title("Show Trips")
    trips_window.geometry("900x600")

    frm = ttk.Frame(trips_window, padding=20)
    frm.grid(row=0, column=0, sticky="nsew")
    trips_window.rowconfigure(0, weight=1)
    trips_window.columnconfigure(0, weight=1)

    # --- date filter ---
    ttk.Label(frm, text="Select Trip Date:").grid(column=0, row=0, sticky=W, pady=5)
    date_var = StringVar(value=datetime.now().strftime("%Y-%m-%d"))
    date_entry = DateEntry(frm, textvariable=date_var, date_pattern="yyyy-mm-dd")
    date_entry.grid(column=1, row=0, pady=5, sticky=W)

    # --- Treeview ---
    columns = ("school", "plate", "student", "boarded_time", "dropoff_time", "json_file")
    tree = ttk.Treeview(frm, columns=columns, show="headings", height=15)
    tree.grid(column=0, row=2, columnspan=3, pady=10, sticky="nsew")

    for col in columns[:-1]:
        tree.heading(col, text=col.capitalize())
        tree.column(col, width=150)

    tree.column("json_file", width=0, stretch=False)  # hide json_file for user

    frm.grid_rowconfigure(2, weight=1)
    frm.grid_columnconfigure(2, weight=1)

    # --- load data from JSON ---
    def load_trips():
        selected_date = date_var.get()

        # clean table
        for row in tree.get_children():
            tree.delete(row)

        trips_dir = Path(__file__).parent / "trips"

        for file in trips_dir.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # filter json by looking at the date in the name
            file_date = file.stem.split("_")[0]  # checks 'YYYY-MM-DD'
            if file_date != selected_date:
                continue

            for st in data["students"]:
                tree.insert("", "end", values=(
                    data.get("school", ""),
                    data.get("plate", ""),
                    st.get("name", ""),
                    st.get("boarded_time", ""),
                    st.get("dropoff_time", ""),
                    str(file)  # file path
                ))

    # command to open trips by selected date
    load_trips()

    ttk.Button(frm, text="View Trips", command=load_trips).grid(column=2, row=0, pady=5, sticky=E)

    # --- show map ---
    def show_map():
        selected = tree.focus()
        if not selected:
            print("First select a trip to view map")
            return

        values = tree.item(selected, "values")
        json_file = values[-1]

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        coords = [(loc["lat"], loc["lng"]) for loc in data["locations"]]

        if not coords:
            print("Missing data for this trip")
            return

        # Trip polyline created with folium map using coords registererd in json file
        m = folium.Map(location=coords[0], zoom_start=15)
        folium.PolyLine(coords, color="blue", weight=3).add_to(m)

        # --- Marker when board ---
        boarded_students = [st["name"] for st in data["students"] if st["boarded_time"]]
        if boarded_students:
            popup_text = "Students on board:\n" + "\n".join(boarded_students)
            # Marker grouped students scans when boarding shuddle
            first_boarded = next(st for st in data["students"] if st["boarded_time"])
            folium.Marker(
                location=[first_boarded["boarded_lat"], first_boarded["boarded_lng"]],
                popup=popup_text,
                icon=folium.Icon(color="green", icon="school")
            ).add_to(m)

        # --- Markers drop off ---
        cluster = MarkerCluster().add_to(m)
        for st in data["students"]:
            if st["dropoff_time"]:
                folium.Marker(
                    [st["dropoff_lat"], st["dropoff_lng"]],
                    popup=f"Bajada: {st['name']}",
                    icon=folium.Icon(color="red", icon="home")
                ).add_to(cluster)

        map_file = "trip_map.html"
        m.save(map_file)
        webbrowser.open(map_file)

    ttk.Button(frm, text="Show Map", command=show_map).grid(column=2, row=1, pady=5, sticky=E)

    # --- buttom close ---
    def close_trips_window(window, parent_window):
        window.destroy()
        parent_window.deiconify()

    ttk.Button(frm, text="Close", command=lambda: close_trips_window(trips_window, parent_window)).grid(column=2, row=3, pady=10, sticky=E)

    trips_window.protocol("WM_DELETE_WINDOW", lambda: close_trips_window(trips_window, parent_window))
    trips_window.grab_set()
    trips_window.focus_force()
    trips_window.wait_window()

# Create window tkinter
def run_main():
    root = Tk()
    root.title("MyShuddle User Administrator")
    root.geometry("500x300")

    # Make root expandable
    root.grid_rowconfigure(0, weight=1)   
    root.grid_columnconfigure(0, weight=1)  

    frm = ttk.Frame(root, padding=50)
    frm.grid(row=0, column=0)

    # Make frm expandable so content centers
    frm.grid_rowconfigure(0, weight=1)
    frm.grid_rowconfigure(1, weight=1)
    frm.grid_columnconfigure(0, weight=1)
    frm.grid_columnconfigure(1, weight=1)

    # Inner frame for login form
    login_box = ttk.Frame(frm, padding=20)
    login_box.grid(row=1, column=1)  # center cell of frm

    # Create inputs for log in
    ttk.Label(login_box, text="Email:").grid(column=0, row=0, sticky=W, pady=5)
    entry_user = ttk.Entry(login_box, width=25)
    entry_user.grid(column=1, row=0, pady=5)

    ttk.Label(login_box, text="Password:").grid(column=0, row=1, sticky=W, pady=5)
    entry_pass = ttk.Entry(login_box, show="*", width=25)
    entry_pass.grid(column=1, row=1, pady=5)

    ttk.Button(login_box, text="Login", command=lambda: login(root, entry_user, entry_pass)).grid(column=0, row=2, columnspan=2, pady=10)
    ttk.Button(login_box, text="Logout", command=root.destroy).grid(column=0, row=3, columnspan=2, pady=5)

    root.mainloop()

run_main()