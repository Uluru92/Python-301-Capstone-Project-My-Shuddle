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

# Login function
def login():
    email = entry_user.get()
    password = entry_pass.get()

    if email == admin_email and password == admin_password:
        messagebox.showinfo("Login Success", f"Welcome, {email}!")
        # 👉 Here you can open the admin dashboard window
    else:
        messagebox.showerror("Login Failed", "Invalid admin credentials.")

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
