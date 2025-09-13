from tkinter import *
from tkinter import ttk
import mysql.connector
from tkinter import messagebox
import os
from dotenv import load_dotenv

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

# Login function
def login():
    email = entry_user.get()
    password = entry_pass.get()

    conn = connect_db()
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT * FROM parents WHERE email=%s AND password=%s", (email, password))
    result = cursor.fetchone()

    if result:
        messagebox.showinfo("Login Success", f"Welcome {email}!")
    else:
        messagebox.showerror("Login Failed", "Invalid email or password.")

    conn.close()

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
