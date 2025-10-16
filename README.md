Python-301 Capstone Project – MyShuddle

MyShuddle is a real-time school bus tracking application that allows parents to monitor their children’s journey safely from school to home.

Features:
- Real-time bus location tracking on a map.
- Track students onboard and their drop-off locations.
- History of trips for analysis.
- Simple interface to manage parents, students, and trips.

Getting Started:
1. Clone the Repository and Setup Environment
git clone <https://github.com/Uluru92/Python-301-Capstone-Project-My-Shuddle.git>
cd Python-301-Capstone-Project-My-Shuddle
python -m venv venv
# Activate venv (Windows)
venv\Scripts\activate
# Activate venv (Mac/Linux)
source venv/bin/activate
pip install -r requirements.txt

2. Create Users via Tkinter Interface
Run the GUI to add parents and students, use this interface to create parent accounts and assign students.: python tkinter_gui_interface.py
Admin credentials (default):
- Email: admin@gmail.com
- Password: admin123

3. Start Flask App and Ngrok

- Generate a public URL with ngrok, open command prompt: ngrok http 5000
- Copy the generated public URL and set it in .env as NGROK_URL. Note: This URL changes every time you restart ngrok.

Run Flask:
python bus_tracker.py


4. Parent Usage

Real-time Tracking: Open a browser and visit:
- Parents log in with their account: <ngrok_url>/parent/login
- Refresh the page every ~30 seconds to see updated bus location.
- See map without credentias: <ngrok_url>/map
- Refresh /parent/login and /map pages to see real-time data.

5. Trip History

- After trips finish, JSON files are saved in trips/.
- View trip history and details via tkinter_gui_interface.py.

Project Structure
Python-301-Capstone-Project-My-Shuddle/
├─ bus_tracker.py          # Main Flask app
├─ tkinter_gui_interface.py# GUI for creating users and viewing history
├─ models.py               # OOP models: Bus, Student, BusLocation
├─ trips/                  # Saved trip JSON files
├─ requirements.txt        # Python dependencies
└─ .env                    # Environment variables

Notes: .env must contain your MySQL credentials and NGROK_URL.