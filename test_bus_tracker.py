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
        self.client = app.test_client() # test flask client

    def test_home_endpoint(self):
        """check endpoint '/' """
        response = self.client.get("/") # request GET simulated
        self.assertEqual(response.status_code,200)      # test if response 200 ok
        self.assertIn(b"<html",response.data.lower())   # test if it is a html structure
        self.assertIn(b"ngrok", response.data.lower())  # test if ngrok is passed in html

if __name__ == "__main__":
    unittest.main()