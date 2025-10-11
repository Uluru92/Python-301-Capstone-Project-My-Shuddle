import unittest
from bus_tracker import *

class TestBusTracker(unittest.TestCase):

    def setUp(self):
        """Get ready to start every test"""
        self.original_bus = getattr(app_state, "current_bus", None)
        app_state.current_bus = None  # Make sure it starts empty
    
    def tearDown(self):
        """restores default value"""
        app_state.current_bus = self.original_bus

    def test_get_db_connection(self):
        conn = get_db_connection()
        self.assertIsNotNone(conn,"failed to connect to DB")

        cursor = conn.cursor()
        cursor.execute("SELECT 1,2,3,4,5")
        result = cursor.fetchall()
        self.assertEqual(result[0][3],4,"The query result should be 3")

        cursor.close()
        conn.close()

    def test_current_bus_uses_default_plate(self):
        """Verifica que se use la placa por defecto si no se pasa argumento"""
        start_new_trip()
        self.assertEqual(app_state.current_bus.plate, "BUS123")

    def test_start_new_trip_current_bus_is_instance_of_Bus(self):
        """Verifica que start_new_trip cree un objeto Bus"""
        plate = "TEST123"
        start_new_trip(plate=plate)

        # test if current_bus is not None
        self.assertIsNotNone(app_state.current_bus)

        # test if new instancia is a Bus object
        self.assertIsInstance(app_state.current_bus, Bus)

        # test if bus is using the correct plate passed as argument
        self.assertEqual(app_state.current_bus.plate, "TEST123")

        # Check if locations is a list
        self.assertIsInstance(app_state.current_bus.locations, list)

        # Check if trip_file path targets to /trips
        self.assertTrue(app_state.current_trip_file.startswith("trips/"))
        self.assertIn(plate, app_state.current_trip_file)

        # Check if trip_in_progress is True
        self.assertTrue(app_state.trip_in_progress)

        # Check if /trips exists
        self.assertTrue(os.path.exists("trips"))

    def test_get_school_name_by_trip(self):
        # set desault trip_id if None
        trip_id = app_state.current_trip_id or 1 
        school_name = get_school_name_by_trip(trip_id)

        # check None if there is no  o un string (si hay viaje)
        if school_name is not None:
            self.assertIsInstance(school_name, str) # if there is a trip recorded, there should be a string
        else:
            self.assertIsNone(school_name) # if there is not trip recorded 
        
    def test_get_students_by_trip(self):
        # set current id to any existing trip
        app_state.current_trip_id = 1
        students = get_students_by_trip(app_state.current_trip_id)

        self.assertIsNotNone(students) 
        self.assertIsInstance(students, list) # students should be a list
        for s in students:
            self.assertIsInstance(s, dict)
            expected_keys = {
                "student_id", "name", "status",
                "boarded_time", "boarded_lat", "boarded_lng",
                "dropoff_time", "dropoff_lat", "dropoff_lng"
            }
            self.assertTrue(expected_keys.issubset(s.keys()))

    def test_get_locations_serializable(self):

        locations_serializable = get_locations_serializable(app_state.current_bus)
        self.assertIsNotNone(locations_serializable)
        self.assertIsInstance(locations_serializable, list) # locations_serializable should be a list
        for locs in locations_serializable:
            self.assertIsInstance(locs, dict) # inside the list should be 1 dictionary for every student

        expected_keys = {
                        "plate",
                        "lat",
                        "lng",
                        "timestamp"
                        }
        for s in locations_serializable:
            self.assertTrue(expected_keys.issubset(s.keys()),)

    def test_save_trip_json_minimal(self):
        trip_data = {
        "trip_id": 1,
        "plate": "TEST123",
        "school": None,
        "students": [],
        "locations": []
    }
        filename = save_filename_trip_json(trip_data)

        # check if file exists
        self.assertTrue(filename.exists())

        # check JSON keys 
        with open(filename, "r", encoding="utf-8") as f:
            data_loaded = json.load(f)
        self.assertTrue(set(data_loaded.keys()) >= {"trip_id","plate","school","students","locations"})

        # clean
        filename.unlink()

class TestFlaskEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()                 # create test flask client
        app_state.trip_in_progress = False
        app_state.current_trip_id = None
        app_state.current_bus = None
        app_state.pre_scanned_students = [
            Student(1, "Jimena Alvarado Araya"),
            Student(2, "Luis Pérez")
        ]
        
    def test_home_endpoint(self):
        """create a test client HTTP to check endpoint '/' """
        response = self.client.get("/")                 # request GET simulated
        self.assertEqual(response.status_code,200)      # test if response 200 ok
        self.assertIn(b"<html",response.data.lower())   # test if it is a html structure
        self.assertIn(b"ngrok", response.data.lower())  # test if ngrok is passed in html

    def test_scan_page(self):
        """"create a test client HTTP, check if endpoint '/scan.html' serves the scan.html content"""
        response = self.client.get("/scan.html")
        data_lower = response.data.lower()              # html structure
        
        self.assertEqual(response.status_code, 200)     # check response 200 ok 
        self.assertIn(b"<input", data_lower)            # search for html structure
        self.assertIn(b"<button", data_lower)           # search for html structure
        self.assertIn(b"sendstudent", data_lower)       # async function spected
        self.assertIn(b"/board_student", data_lower)    # await fetch -> endpoint

    def test_board_student(self):
        """Check endpoint '/board_student' POST method"""
        app_state.pre_scanned_students.clear()          # clean pre scanned memory
        
        payload = {                                     # Simulated data of a Student
            "student_id": 101,
            "name": "Jimena Alvarado Araya",
            "lat": 9.999,
            "lng": -85.345,
            "timestamp": "2025-10-09T15:10:00Z"
        }
  
        response = self.client.post("/board_student", json=payload) 
        self.assertEqual(response.status_code, 200)     # check response 200 ok 

        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["student"]["student_id"], 101)
        self.assertEqual(data["student"]["name"], "Jimena Alvarado Araya")
        self.assertEqual(data["student"]["status"], "onboard")

        # check if student saved in pre scanned students memory
        self.assertTrue(any(s.student_id == 101 for s in app_state.pre_scanned_students))

        # try catching error when same student sent twice
        response2 = self.client.post("/board_student", json=payload)
        self.assertEqual(response2.status_code, 200)

        data2 = response2.get_json()
        self.assertEqual(data2["status"], "warning")
        self.assertIn("was already scanned", data2["message"])

    def test_get_boarded_students_no_trip(self):
        """Should return pre-scanned students if no trip active"""
        app_state.trip_in_progress = False
        app_state.pre_scanned_students = [
            Student(10, "Mario López"),
            Student(11, "Lucía Vargas")
        ]

        res = self.client.get("/get_boarded_students")
        data = res.get_json()

        # check status code, list pre scanned students memory
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertIn("Mario López", [s["name"] for s in data])

    def test_start_trip(self):
        """Check endpoint '/start_trip' POST method"""
        # fill the pre scanned memory to check endpoint /start_trip
        app_state.pre_scanned_students = [
            Student(1, "Jimena Alvarado Araya"),
            Student(2, "Luis Pérez")
        ]
        for s in app_state.pre_scanned_students:
            s.status = "onboard"
            s.boarded_time = "2025-10-09 15:00:00"
            s.boarded_lat = 9.999
            s.boarded_lng = -85.345

        # check petition response
        response = self.client.post("/start_trip")
        self.assertEqual(response.status_code, 200)

        # check json response expected
        data = response.get_json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("trip_id", data)
        self.assertIn("message", data)
        self.assertIn("iniciado", data["message"].lower())

        # check some atributes of app_state that should change
        self.assertTrue(app_state.trip_in_progress)
        self.assertIsNotNone(app_state.current_trip_id)
        self.assertIsNotNone(app_state.current_bus)
        self.assertEqual(len(app_state.current_bus.students_onboard), 2)

        # check if pre-scanned memory is clean
        self.assertEqual(len(app_state.pre_scanned_students), 0)

    def test_start_trip_already_in_progress(self):
        """Should not be able to start if there is an ongoing active trip"""
        app_state.trip_in_progress = True  # Simulated trip

        response = self.client.post("/start_trip")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()

        self.assertIn("status", data)
        self.assertEqual(data["status"], "error")
        self.assertIn("ya está en curso", data["message"])

    def test_start_trip_with_no_students(self):
        """should not initiate a trip without pre scanned students memory"""
        app_state.trip_in_progress = False
        app_state.pre_scanned_students = []

        response = self.client.post("/start_trip")
        self.assertEqual(response.status_code, 400)
        
        data = response.get_json()
        self.assertEqual(data["status"], "error")
        self.assertIn("There are no students on board, cannot start the trip", data["message"])

    def test_stop_trip_success(self):
        """Create a fictional trip without students onboard"""
        conn = get_db_connection()
        cursor = conn.cursor()

        # creates fictional school
        cursor.execute("""
            INSERT IGNORE INTO schools (school_phone, school_name, school_address)
            VALUES ('12345678', 'Test School', '123 Test Street')
        """)

        # creates fictional bus
        cursor.execute("""
            INSERT IGNORE INTO buses (plate, driver_name, driver_phone, attendant_name, attendant_phone)
            VALUES ('BUS-002', 'Test Driver', '88888888', 'Test Attendant', '77777777')
        """)

        # creates fictional student
        cursor.execute("""
            INSERT IGNORE INTO students (student_id, parent_email, first_name, last_name, birth_date, school_phone)
            VALUES (2000, NULL, 'Fictional', 'Student', '2015-01-01', '12345678')
        """)

        # creates fictional trip
        cursor.execute("""
            INSERT INTO trips (trip_id, plate, school_phone, trip_date, departure_time)
            VALUES (1000, 'BUS-002', '12345678', CURDATE(), CURTIME())
        """)

        # create a dropped off student
        cursor.execute("""
            INSERT INTO trip_students (trip_id, student_id, status)
            VALUES (1000, 2000, 'dropped_off')
        """)

        conn.commit()

        # simulate trip in progress
        app_state.trip_in_progress = True
        app_state.current_trip_id = 1000

        # execute endpoint
        res = self.client.post("/stop_trip")
        data = res.get_json()

        # check data received
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["status"], "ok")
        self.assertIn("Trip stopped.", data["message"])
        self.assertFalse(app_state.trip_in_progress)
        self.assertIsNone(app_state.current_trip_id)

        # clean data before finishing
        cursor.execute("DELETE FROM trip_students WHERE trip_id = 1000")
        cursor.execute("DELETE FROM trips WHERE trip_id = 1000")
        cursor.execute("DELETE FROM students WHERE student_id = 2000")
        cursor.execute("DELETE FROM buses WHERE plate = 'BUS-002'")
        cursor.execute("DELETE FROM schools WHERE school_phone = '12345678'")
        conn.commit()

        cursor.close()
        conn.close()

    def test_alight_student(self):
        """Check endpoint '/alight_student' POST method"""
        # simulates a current trip with a studiante on board
        app_state.trip_in_progress = True
        app_state.current_trip_id = 500
        student = Student(1, "Jimena Alvarado Araya")
        student.status = "onboard"
        app_state.current_bus = Bus("BUS-001")
        app_state.current_bus.students_onboard = [student]

        payload = {
            "student_id": 1,
            "lat": 9.999,
            "lng": -85.345,
            "timestamp": "2025-10-10T15:30:00Z"
        }

        res = self.client.post("/alight_student", json=payload)
        data = res.get_json()

        # check status codes, status and message received
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["status"], "ok")
        self.assertIn("Student dropped off", data["message"])
        self.assertEqual(app_state.current_bus.students_onboard[0].status, "dropped_off")

    def test_location_endpoint(self):
        """Check endpoint '/location' adds new coordinates"""
        app_state.trip_in_progress = True
        app_state.current_bus = Bus("BUS-LOC-01")

        payload = {
            "lat": 9.888,
            "lng": -85.333,
            "timestamp": "2025-10-10T15:45:00Z"
        }

        res = self.client.post("/location", json=payload)
        data = res.get_json()

        # check status code, status, plate, locations
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["plate"], "BUS-LOC-01")
        self.assertEqual(len(app_state.current_bus.locations), 1)

if __name__ == "__main__":
    unittest.main()